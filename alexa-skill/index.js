'use strict';

var http = require('http');


var versesPerChapter = [
[31,25,24,26,32,22,24,22,29,32,32,20,18,24,21,17,27,33,38,18,34,24,20,67,34,35,46,22,35,43,54,33,20,31,29,43,36,30,23,23,57,38,34,34,28,34,31,22,33,26],
[22,25,22,31,23,30,29,28,35,29,10,51,22,31,27,36,16,27,25,23,37,30,33,18,40,37,21,43,46,38,18,35,23,35,35,38,29,31,43],
[17,16,17,35,26,23,38,36,24,20,47,8,59,57,33,34,16,30,37,27,24,33,44,23,55,46,34],
[54,34,51,49,31,27,89,26,23,36,35,16,33,45,41,35,28,32,22,29,35,41,30,25,18,65,23,31,39,17,54,42,56,29,34,13],
[46,37,29,49,30,25,26,20,29,22,32,31,19,29,23,22,20,22,21,20,23,29,26,22,19,19,26,69,28,20,30,52,29,12],
];

var englishBookNames = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"];

var engBookName = {'genesis' : 0, 
                   'exodus' : 1,
                   'leviticus' : 2,
                   'numbers' : 3,
                   'deuteronomy' : 4};

// sample ORT MP3: https://scrollscraper.adatshalom.net/ORT_MP3s.recoded/t1/2219.mp3

var mp3base = "https://scrollscraper.adatshalom.net/ORT_MP3s.recoded/t{0}/{1}{2}.mp3";


exports.handler = function(event,context) {

  try {

    if(process.env.NODE_DEBUG_EN) {
      console.log("Request:\n"+JSON.stringify(event,null,2));
    }



    var request = event.request;
    var session = event.session;

    if(!event.session.attributes) {
      event.session.attributes = {};
    }

    /*
      i)   LaunchRequest       Ex: "Open scrollscraper"
      ii)  IntentRequest       Ex: "Ask Scrollscraper to chant Genesis Chapter 7 verses 3 through 8"
      iii) SessionEndedRequest Ex: "exit" or error or timeout
    */

    if (request.type === "LaunchRequest") {
      handleLaunchRequest(context);

    } else if (request.type === "IntentRequest") {

      if (request.intent.name === "ChantIntent" || request.intent.name === "ScrollScraper") {

        handleChantIntent(request,context);

      } else if (request.intent.name === "WhenIsParshaReadIntent") {

        handleWhenIsParshaReadIntent(request,context,session);

      } else if (request.intent.name === "AMAZON.StopIntent" || request.intent.name === "AMAZON.CancelIntent") {
        context.succeed(buildResponse({
          speechText: "Good bye. ",
          endSession: true
        }));

      } else {
        throw "Unknown intent";
      }

    } else if (request.type === "SessionEndedRequest") {

    } else {
      throw "Unknown intent type";
    }
  } catch(e) {
    context.fail("Exception: "+e);
  }

}


function buildResponse(options) {
  let speakText = options.speechText;

  if(process.env.NODE_DEBUG_EN) {
    console.log("buildResponse options:\n"+JSON.stringify(options,null,2));
  }

  if (options.audioString) {
      speakText += options.audioString;
  }

  var response = {
    version: "1.0",
    response: {
      outputSpeech: {
        type: "SSML",
        ssml: "<speak>"+speakText+"</speak>"
      },
      shouldEndSession: options.endSession
    }
  };

  if(options.repromptText) {
    response.response.reprompt = {
      outputSpeech: {
        type: "SSML",
        ssml: "<speak>"+options.repromptText+"</speak>"
      }
    };
  }

  if(options.cardTitle) {
    response.response.card = {
      type: "Simple",
      title: options.cardTitle
    }

    if(options.imageUrl) {
      response.response.card.type = "Standard";
      response.response.card.text = options.cardContent;
      response.response.card.image = {
        smallImageUrl: options.imageUrl,
        largeImageUrl: options.imageUrl
      };

    } else {
      response.response.card.content = options.cardContent;
    }
  }


  if(options.session && options.session.attributes) {
    response.sessionAttributes = options.session.attributes;
  }

  if(process.env.NODE_DEBUG_EN) {
    console.log("Response:\n"+JSON.stringify(response,null,2));
  }

  return response;
}

function handleLaunchRequest(context) {
  let options = {};
  options.speechText =  "Welcome to the Scroll Scraper skill. Using our skill you can listen to and practice your scheduled Torah reading."
  options.repromptText = "You can say for example, Chant Genesis Chapter 7 verses 11 through 14. ";
  options.endSession = false;
  context.succeed(buildResponse(options));
}

function handleChantIntent(request,context) {
  let options = {};
  let bookName = request.intent.slots.TorahBooks.value.toLowerCase();
  let bookValue = engBookName[bookName] + 1;
  let startc = request.intent.slots.StartChapter.value;
  let startv = request.intent.slots.StartVerse.value;
  let endc = request.intent.slots.EndChapter.value;
  let endv = request.intent.slots.EndVerse.value;
  let undefinedStuff = "";

  if (typeof(bookName) === 'undefined') {
      undefinedStuff += "Book name was not heard. ";
  }
  if (typeof(startc) === 'undefined') {
      undefinedStuff += "Starting chapter was not heard. ";
  }
  if (typeof(startv) === 'undefined') {
      undefinedStuff += "Starting verse was not heard. ";
  }
  if (typeof(endv) === 'undefined') {
      undefinedStuff += "Ending verse was not heard. ";
  }

  if (undefinedStuff) {
     options.speechText = undefinedStuff;
  } else {
      if (typeof(endc) === 'undefined') {
          endc = startc;
      }
    
      let scrollscraperURL = "https://scrollscraper.adatshalom.net/scrollscraper.cgi?book=" + bookValue + "&doShading=on&startc=" + startc + "&startv=" + startv + "&endc=" + endc + "&endv=" + endv;
      options.cardTitle = bookName + " " + startc + ":" + startv + " - " + endc + ":" + endv;
      
    
      options.speechText = "This is an excerpt from " + bookName +  ", Chapter " + startc;
      if (startc === endc) {
          options.speechText += " verses " + startv + " through " + endv;
      } else {
          options.speechText += " verse " + startv + " through chapter " + endc + " verse " + endv;
      }
      options.speechText += ". The following recorded materials are copyright world-ORT, 1997, all rights reserved.";
      options.cardContent = scrollscraperURL;
    
      options.audioString = chaptersAndVerses2AudioString(bookValue,startc,startv,endc,endv);

      // test value for now
      options.imageUrl = "https://scrollscraper.adatshalom.net/colorImage.cgi?thegif=/webmedia/t1/0103C111.gif&coloring=0,0,0,0,0,0";
  }

  context.succeed(buildResponse(options));
}


// all parameters are 1-based below
function tomp3url(book,chapter,verse) {
//   return "https://scrollscraper.adatshalom.net/ORT_MP3s.recoded/t" + book + "/" + chapter.toString().padStart(2,'0') + verse.toString().padStart(2,'0') + ".mp3";
//   n.toLocaleString('en', {minimumIntegerDigits:4
   return "https://scrollscraper.adatshalom.net/ORT_MP3s.recoded/t" + book + "/" + chapter.toLocaleString('en', {minimumIntegerDigits:2}) + verse.toLocaleString('en', {minimumIntegerDigits:2}) + ".mp3";
}

// TODO: check for off-by-one errors
function chaptersAndVerses2AudioString(book,startc,startv,endc,endv) {
  let count = 0;
  let maxFetches = 100;
  let c = startc;
  let v = startv;
  let retval = "";
  let chaptersInBook = versesPerChapter[book-1].length;

  // <audio src="https://carfu.com/audio/carfu-welcome.mp3" /> 
  while (count++ <  maxFetches) {
    if ((c < chaptersInBook && c < endc) || ((c == chaptersInBook || c == endc) && v <= endv)) {
      retval += '<audio src="' + tomp3url(book,c,v) + '" />';
      v++;
      if (v > versesPerChapter[book-1][c-1]) {
         v = 1;
         c++;
      }
    }
  }

  return retval;
}
