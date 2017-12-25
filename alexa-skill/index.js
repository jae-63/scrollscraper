'use strict';


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

var mostVersesPerMp3 = 4;

var maxAudioSegments = 5;

var missingMp3s = {
        '1/0126_4' : 1,
        '1/0127_4' : 1,
        '1/0128_4' : 1,
        '1/0305_4' : 1,
        '1/0314_4' : 1,
        '1/0818_4' : 1,
        '1/0819_4' : 1,
        '1/0820_4' : 1,
        '1/0821_4' : 1,
        '1/1720_4' : 1,
        '1/1914_4' : 1,
        '1/1919_4' : 1,
        '1/2006_4' : 1,
        '1/2114_4' : 1,
        '1/2201_4' : 1,
        '1/2202_4' : 1,
        '1/2407_4' : 1,
        '1/2412_4' : 1,
        '1/2413_4' : 1,
        '1/2414_4' : 1,
        '1/2445_4' : 1,
        '1/2446_4' : 1,
        '1/2607_4' : 1,
        '1/2730_4' : 1,
        '1/2736_4' : 1,
        '1/2812_4' : 1,
        '1/2813_4' : 1,
        '1/3013_4' : 1,
        '1/3014_4' : 1,
        '1/3030_4' : 1,
        '1/3035_4' : 1,
        '1/3131_4' : 1,
        '1/3132_4' : 1,
        '1/3133_4' : 1,
        '1/3140_4' : 1,
        '1/3141_4' : 1,
        '1/3208_4' : 1,
        '1/3707_4' : 1,
        '1/3905_4' : 1,
        '1/4315_4' : 1,
        '1/4414_4' : 1,
        '1/4415_4' : 1,
        '1/4416_4' : 1,
        '1/4715_4' : 1,
        '1/4716_4' : 1,
        '1/4717_3' : 1,
        '1/4717_4' : 1,
        '1/4718_4' : 1,
        '1/4726_4' : 1,
        '1/4804_4' : 1,
        '1/4813_4' : 1,
        '1/4814_4' : 1,
        '1/4815_4' : 1,
        '1/4816_4' : 1,
        '1/4817_4' : 1,
        '1/4928_4' : 1,
        '1/5010_4' : 1,
        '2/0305_4' : 1,
        '2/0306_4' : 1,
        '2/0312_4' : 1,
        '2/0313_4' : 1,
        '2/0314_3' : 1,
        '2/0314_4' : 1,
        '2/0315_3' : 1,
        '2/0315_4' : 1,
        '2/0316_3' : 1,
        '2/0316_4' : 1,
        '2/0317_4' : 1,
        '2/0407_4' : 1,
        '2/0408_4' : 1,
        '2/0409_4' : 1,
        '2/0418_4' : 1,
        '2/0605_4' : 1,
        '2/0606_4' : 1,
        '2/0716_4' : 1,
        '2/0717_4' : 1,
        '2/0718_4' : 1,
        '2/0719_4' : 1,
        '2/0814_4' : 1,
        '2/0815_4' : 1,
        '2/0816_4' : 1,
        '2/0817_4' : 1,
        '2/0822_4' : 1,
        '2/0922_4' : 1,
        '2/0935_4' : 1,
        '2/1002_4' : 1,
        '2/1003_4' : 1,
        '2/1004_4' : 1,
        '2/1005_4' : 1,
        '2/1006_4' : 1,
        '2/1010_4' : 1,
        '2/1011_4' : 1,
        '2/1012_4' : 1,
        '2/1013_3' : 1,
        '2/1013_4' : 1,
        '2/1014_4' : 1,
        '2/1101_4' : 1,
        '2/1211_4' : 1,
        '2/1212_4' : 1,
        '2/1213_4' : 1,
        '2/1214_4' : 1,
        '2/1215_4' : 1,
        '2/1216_4' : 1,
        '2/1217_4' : 1,
        '2/1219_4' : 1,
        '2/1220_4' : 1,
        '2/1226_4' : 1,
        '2/1227_4' : 1,
        '2/1228_4' : 1,
        '2/1312_4' : 1,
        '2/1313_4' : 1,
        '2/1314_4' : 1,
        '2/1315_4' : 1,
        '2/1316_4' : 1,
        '2/1410_4' : 1,
        '2/1419_4' : 1,
        '2/1525_4' : 1,
        '2/1819_4' : 1,
        '2/2207_4' : 1,
        '2/2519_4' : 1,
        '2/2520_4' : 1,
        '2/2531_4' : 1,
        '2/2532_4' : 1,
        '2/2718_4' : 1,
        '2/2719_4' : 1,
        '2/2720_4' : 1,
        '2/2721_4' : 1,
        '2/2809_4' : 1,
        '2/2826_4' : 1,
        '2/2827_4' : 1,
        '2/2918_4' : 1,
        '2/2919_4' : 1,
        '2/2920_3' : 1,
        '2/2920_4' : 1,
        '2/2921_4' : 1,
        '2/3113_4' : 1,
        '2/3114_4' : 1,
        '2/3116_4' : 1,
        '2/3117_4' : 1,
        '2/3210_4' : 1,
        '2/3211_4' : 1,
        '2/3212_4' : 1,
        '2/3310_4' : 1,
        '2/3311_4' : 1,
        '2/3407_4' : 1,
        '2/3408_4' : 1,
        '2/3409_4' : 1,
        '2/3426_4' : 1,
        '2/3434_4' : 1,
        '2/3519_4' : 1,
        '2/3520_4' : 1,
        '2/3521_3' : 1,
        '2/3521_4' : 1,
        '2/3522_4' : 1,
        '2/3533_4' : 1,
        '2/3534_4' : 1,
        '2/3535_3' : 1,
        '2/3535_4' : 1,
        '2/3601_3' : 1,
        '2/3601_4' : 1,
        '2/3602_4' : 1,
        '2/3603_4' : 1,
        '2/3605_4' : 1,
        '2/3606_4' : 1,
        '2/3608_4' : 1,
        '2/3609_4' : 1,
        '2/3716_4' : 1,
        '2/3717_4' : 1,
        '2/3718_4' : 1,
        '2/3719_4' : 1,
        '2/3815_4' : 1,
        '2/3817_4' : 1,
        '2/3821_4' : 1,
        '2/3822_4' : 1,
        '2/3823_4' : 1,
        '2/3824_4' : 1,
        '2/3825_4' : 1,
        '2/3918_4' : 1,
        '2/3919_4' : 1,
        '3/0111_4' : 1,
        '3/0116_4' : 1,
        '3/0117_4' : 1,
        '3/0402_4' : 1,
        '3/0434_4' : 1,
        '3/0435_4' : 1,
        '3/0501_4' : 1,
        '3/0502_4' : 1,
        '3/0503_4' : 1,
        '3/0504_4' : 1,
        '3/0506_4' : 1,
        '3/0508_4' : 1,
        '3/0509_4' : 1,
        '3/0510_4' : 1,
        '3/0515_4' : 1,
        '3/0521_4' : 1,
        '3/0522_4' : 1,
        '3/0523_4' : 1,
        '3/0602_4' : 1,
        '3/0718_4' : 1,
        '3/0821_4' : 1,
        '3/0822_4' : 1,
        '3/0823_4' : 1,
        '3/0824_4' : 1,
        '3/0828_4' : 1,
        '3/1003_4' : 1,
        '3/1011_4' : 1,
        '3/1012_4' : 1,
        '3/1013_4' : 1,
        '3/1014_4' : 1,
        '3/1015_4' : 1,
        '3/1132_4' : 1,
        '3/1302_4' : 1,
        '3/1303_4' : 1,
        '3/1304_4' : 1,
        '3/1323_4' : 1,
        '3/1325_4' : 1,
        '3/1330_4' : 1,
        '3/1331_4' : 1,
        '3/1351_4' : 1,
        '3/1352_4' : 1,
        '3/1353_4' : 1,
        '3/1355_4' : 1,
        '3/1406_4' : 1,
        '3/1407_4' : 1,
        '3/1408_4' : 1,
        '3/1409_4' : 1,
        '3/1410_4' : 1,
        '3/1411_4' : 1,
        '3/1523_4' : 1,
        '3/1602_4' : 1,
        '3/1612_4' : 1,
        '3/1613_4' : 1,
        '3/1614_4' : 1,
        '3/1615_4' : 1,
        '3/1702_4' : 1,
        '3/1703_4' : 1,
        '3/1704_4' : 1,
        '3/2002_4' : 1,
        '3/2201_4' : 1,
        '3/2202_3' : 1,
        '3/2202_4' : 1,
        '3/2203_4' : 1,
        '3/2318_4' : 1,
        '3/2319_4' : 1,
        '3/2336_4' : 1,
        '3/2337_4' : 1,
        '3/2338_4' : 1,
        '3/2508_4' : 1,
        '3/2527_4' : 1,
        '3/2528_4' : 1,
        '3/2641_4' : 1,
        '3/2642_4' : 1,
        '3/2643_4' : 1,
        '4/0336_4' : 1,
        '4/0338_4' : 1,
        '4/0406_4' : 1,
        '4/0411_4' : 1,
        '4/0412_4' : 1,
        '4/0413_4' : 1,
        '4/0414_3' : 1,
        '4/0414_4' : 1,
        '4/0424_4' : 1,
        '4/0425_4' : 1,
        '4/0512_4' : 1,
        '4/0515_4' : 1,
        '4/0517_4' : 1,
        '4/0518_4' : 1,
        '4/0519_4' : 1,
        '4/0617_4' : 1,
        '4/0618_4' : 1,
        '4/0784_4' : 1,
        '4/0785_4' : 1,
        '4/0786_4' : 1,
        '4/0787_4' : 1,
        '4/0816_4' : 1,
        '4/0817_4' : 1,
        '4/0818_4' : 1,
        '4/0819_4' : 1,
        '4/0903_4' : 1,
        '4/0904_4' : 1,
        '4/0905_4' : 1,
        '4/0910_4' : 1,
        '4/0911_4' : 1,
        '4/0912_4' : 1,
        '4/0913_4' : 1,
        '4/1008_4' : 1,
        '4/1009_4' : 1,
        '4/1115_4' : 1,
        '4/1116_3' : 1,
        '4/1116_4' : 1,
        '4/1117_4' : 1,
        '4/1118_4' : 1,
        '4/1119_4' : 1,
        '4/1123_4' : 1,
        '4/1124_4' : 1,
        '4/1125_4' : 1,
        '4/1129_4' : 1,
        '4/1130_4' : 1,
        '4/1131_4' : 1,
        '4/1319_4' : 1,
        '4/1320_4' : 1,
        '4/1326_4' : 1,
        '4/1329_4' : 1,
        '4/1330_4' : 1,
        '4/1332_4' : 1,
        '4/1413_4' : 1,
        '4/1433_4' : 1,
        '4/1522_4' : 1,
        '4/1523_3' : 1,
        '4/1523_4' : 1,
        '4/1524_4' : 1,
        '4/1538_4' : 1,
        '4/1612_4' : 1,
        '4/1613_4' : 1,
        '4/1614_4' : 1,
        '4/1615_4' : 1,
        '4/1626_4' : 1,
        '4/1627_4' : 1,
        '4/1702_4' : 1,
        '4/1703_3' : 1,
        '4/1703_4' : 1,
        '4/1704_4' : 1,
        '4/1705_4' : 1,
        '4/1720_4' : 1,
        '4/1721_4' : 1,
        '4/1804_4' : 1,
        '4/1805_4' : 1,
        '4/1806_4' : 1,
        '4/1807_3' : 1,
        '4/1807_4' : 1,
        '4/1808_4' : 1,
        '4/1809_4' : 1,
        '4/1815_4' : 1,
        '4/1816_4' : 1,
        '4/1817_4' : 1,
        '4/1818_4' : 1,
        '4/1819_4' : 1,
        '4/1823_4' : 1,
        '4/1910_4' : 1,
        '4/1917_4' : 1,
        '4/1918_4' : 1,
        '4/2010_4' : 1,
        '4/2202_4' : 1,
        '4/2203_4' : 1,
        '4/2204_3' : 1,
        '4/2204_4' : 1,
        '4/2205_4' : 1,
        '4/2217_4' : 1,
        '4/2220_4' : 1,
        '4/2230_4' : 1,
        '4/2235_4' : 1,
        '4/3502_4' : 1,
        '4/3503_4' : 1,
        '4/3505_4' : 1,
        '4/3533_4' : 1,
        '4/3534_4' : 1,
        '4/3601_4' : 1,
        '5/0119_4' : 1,
        '5/0204_4' : 1,
        '5/0205_4' : 1,
        '5/0206_4' : 1,
        '5/0207_4' : 1,
        '5/0236_4' : 1,
        '5/0310_4' : 1,
        '5/0311_4' : 1,
        '5/0317_4' : 1,
        '5/0318_4' : 1,
        '5/0319_4' : 1,
        '5/0401_4' : 1,
        '5/0403_4' : 1,
        '5/0405_4' : 1,
        '5/0406_4' : 1,
        '5/0407_4' : 1,
        '5/0408_3' : 1,
        '5/0408_4' : 1,
        '5/0409_4' : 1,
        '5/0410_4' : 1,
        '5/0418_4' : 1,
        '5/0419_4' : 1,
        '5/0425_4' : 1,
        '5/0431_4' : 1,
        '5/0432_3' : 1,
        '5/0432_4' : 1,
        '5/0433_4' : 1,
        '5/0434_4' : 1,
        '5/0437_4' : 1,
        '5/0438_4' : 1,
        '5/0439_4' : 1,
        '5/0512_4' : 1,
        '5/0513_4' : 1,
        '5/0514_3' : 1,
        '5/0514_4' : 1,
        '5/0515_4' : 1,
        '5/0516_4' : 1,
        '5/0518_4' : 1,
        '5/0519_4' : 1,
        '5/0520_4' : 1,
        '5/0521_4' : 1,
        '5/0522_4' : 1,
        '5/0523_4' : 1,
        '5/0530_4' : 1,
        '5/0624_4' : 1,
        '5/0706_4' : 1,
        '5/0710_4' : 1,
        '5/0712_4' : 1,
        '5/0725_4' : 1,
        '5/0726_4' : 1,
        '5/0801_3' : 1,
        '5/0801_4' : 1,
        '5/0802_4' : 1,
        '5/0901_4' : 1,
        '5/0902_4' : 1,
        '5/0903_3' : 1,
        '5/0903_4' : 1,
        '5/0904_3' : 1,
        '5/0904_4' : 1,
        '5/0905_3' : 1,
        '5/0905_4' : 1,
        '5/0906_4' : 1,
        '5/0907_4' : 1,
        '5/0908_4' : 1,
        '5/0909_4' : 1,
        '5/0910_4' : 1,
        '5/0916_4' : 1,
        '5/0918_4' : 1,
        '5/1008_4' : 1,
        '5/1009_4' : 1,
        '5/1010_4' : 1,
        '5/1121_4' : 1,
        '5/1122_4' : 1,
        '5/1127_4' : 1,
        '5/1128_4' : 1,
        '5/1131_4' : 1,
        '5/1132_4' : 1,
        '5/1201_4' : 1,
        '5/1208_4' : 1,
        '5/1209_4' : 1,
        '5/1210_3' : 1,
        '5/1210_4' : 1,
        '5/1211_4' : 1,
        '5/1215_4' : 1,
        '5/1217_4' : 1,
        '5/1218_4' : 1,
        '5/1220_4' : 1,
        '5/1227_4' : 1,
        '5/1228_4' : 1,
        '5/1229_4' : 1,
        '5/1303_4' : 1,
        '5/1304_3' : 1,
        '5/1304_4' : 1,
        '5/1305_3' : 1,
        '5/1305_4' : 1,
        '5/1306_3' : 1,
        '5/1306_4' : 1,
        '5/1316_4' : 1,
        '5/1421_4' : 1,
        '5/1423_4' : 1,
        '5/1424_4' : 1,
        '5/1426_4' : 1,
        '5/1504_4' : 1,
        '5/1506_4' : 1,
        '5/1507_4' : 1,
        '5/1508_4' : 1,
        '5/1509_4' : 1,
        '5/1601_4' : 1,
        '5/1613_4' : 1,
        '5/1614_4' : 1,
        '5/1615_4' : 1,
        '5/1705_4' : 1,
        '5/1708_4' : 1,
        '5/1709_4' : 1,
        '5/1718_4' : 1,
        '5/1903_4' : 1,
        '5/1904_4' : 1,
        '5/1905_4' : 1,
        '5/1906_4' : 1,
        '5/2005_4' : 1,
        '5/2017_4' : 1,
        '5/2018_4' : 1,
        '5/2221_4' : 1,
        '5/2222_4' : 1,
        '5/2223_4' : 1,
        '5/2224_4' : 1,
        '5/2401_4' : 1,
        '5/2402_4' : 1,
        '5/2518_4' : 1,
        '5/2519_4' : 1,
        '5/2601_4' : 1,
        '5/2602_4' : 1,
        '5/2610_4' : 1,
        '5/2611_4' : 1,
        '5/2612_4' : 1,
        '5/2613_4' : 1,
        '5/2614_4' : 1,
        '5/2619_4' : 1,
        '5/2701_4' : 1,
        '5/2702_4' : 1,
        '5/2810_4' : 1,
        '5/2811_4' : 1,
        '5/2812_4' : 1,
        '5/2851_4' : 1,
        '5/2852_4' : 1,
        '5/2855_4' : 1,
        '5/2862_4' : 1,
        '5/2867_4' : 1,
        '5/2868_4' : 1,
        '5/2914_4' : 1,
        '5/2915_4' : 1,
        '5/2916_4' : 1,
        '5/2917_3' : 1,
        '5/2917_4' : 1,
        '5/2918_4' : 1,
        '5/2919_4' : 1,
        '5/2920_4' : 1,
        '5/2921_4' : 1,
        '5/2928_4' : 1,
        '5/3009_4' : 1,
        '5/3017_4' : 1,
        '5/3019_4' : 1,
        '5/3020_4' : 1,
        '5/3105_4' : 1,
        '5/3106_4' : 1,
        '5/3107_4' : 1,
        '5/3109_4' : 1,
        '5/3110_4' : 1,
        '5/3111_4' : 1,
        '5/3112_3' : 1,
        '5/3112_4' : 1,
        '5/3113_4' : 1,
        '5/3114_4' : 1,
        '5/3115_4' : 1,
        '5/3116_4' : 1,
        '5/3117_4' : 1,
        '5/3118_4' : 1,
        '5/3119_3' : 1,
        '5/3119_4' : 1,
        '5/3120_4' : 1,
        '5/3121_4' : 1,
        '5/3126_4' : 1,
        '5/3127_4' : 1,
        '5/3249_4' : 1
};


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
  let bookName = request.intent.slots.TorahBooks.value;
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

  if (undefinedStuff != "") {
     options.speechText = undefinedStuff;
  } else {
      let bookName = request.intent.slots.TorahBooks.value.toLowerCase();
      let bookValue = engBookName[bookName] + 1;

      if (typeof(endc) === 'undefined') {
          endc = startc;
      }
    
      let numOmittedVerses = 0;
      let numVersesUsed = 0;
      let scrollscraperURL = "https://scrollscraper.adatshalom.net/scrollscraper.cgi?book=" + bookValue + "&doShading=on&startc=" + startc + "&startv=" + startv + "&endc=" + endc + "&endv=" + endv;
      options.cardTitle = bookName + " " + startc + ":" + startv + " - " + endc + ":" + endv;
      
    
      // TODO: If numOmittedVerses is non-zero then modify options.speechText to inform the user
      [numOmittedVerses,numVersesUsed,options.audioString] = chaptersAndVerses2AudioString(bookValue,startc,startv,endc,endv);

      if (numOmittedVerses > 0) {
          options.speechText = "This is a truncated excerpt of " + numVersesUsed + " verses from " + bookName +  ", Chapter " + startc;
      } else {
          options.speechText = "This is an excerpt from " + bookName +  ", Chapter " + startc;
      }
      if (startc === endc) {
          options.speechText += " verses " + startv + " through " + endv;
      } else {
          options.speechText += " verse " + startv + " through chapter " + endc + " verse " + endv;
      }
      options.speechText += ". The following recorded materials are copyright world-ORT, 1997, all rights reserved.";
      options.cardContent = scrollscraperURL;
    
      // test value for now
      options.imageUrl = "https://scrollscraper.adatshalom.net/colorImage.cgi?thegif=/webmedia/t1/0103C111.gif&coloring=0,0,0,0,0,0";
  }

  context.succeed(buildResponse(options));
}


// all parameters are 1-based below
function tomp3url(book,chapter,verse,maxVerses) {
//   return "https://scrollscraper.adatshalom.net/ORT_MP3s.recoded/t" + book + "/" + chapter.toString().padStart(2,'0') + verse.toString().padStart(2,'0') + ".mp3";
//   n.toLocaleString('en', {minimumIntegerDigits:4
   if (maxVerses > mostVersesPerMp3) {
       maxVerses = mostVersesPerMp3;
   }
   let formattedChapter = ("0" + chapter).slice(-2);
   let formattedVerse = ("0" + verse).slice(-2);
   let baseString = book + "/" + formattedChapter + formattedVerse;
   let prefix = "https://scrollscraper.adatshalom.net/ORT_MP3s.recoded/t";

   while (maxVerses > 1) {
     let nameWithSuffix = baseString + "_" + maxVerses;
     if (! missingMp3s[nameWithSuffix]) {
       return [maxVerses,prefix + nameWithSuffix + ".mp3"];
     }
     maxVerses--;
   }
   return [1, prefix + baseString + ".mp3"];
}

// TODO: check for off-by-one errors
function chaptersAndVerses2AudioString(book,startc,startv,endc,endv) {
  let count = 0;
  let count2 = 0;
  let maxFetches = 100;
  let c = startc;
  let v = startv;
  let retval = "";
  let chaptersInBook = versesPerChapter[book-1].length;
  let versesUsed = 0;
  let mp3url = "";
  let totalVersesUsed = 0;

  // <audio src="https://carfu.com/audio/carfu-welcome.mp3" /> 

  // On the first pass compute how many total verses are requested in the reading
  while (count2++ <  maxFetches) {
    if ((c < chaptersInBook && c < endc) || ((c == chaptersInBook || c == endc) && v <= endv)) {
      count++;
      v++;
      if (v > versesPerChapter[book-1][c-1]) {
         v = 1;
         c++;
      }
    }
  }

  c = startc;
  v = startv;

  let totalNumRequestedVerses = count;

  let numAudioSegments = 0;

  // now on the second pass using the longest mp3s available which don't overrun the end of our
  // reading.    TODO: also make sure that we don't overrun AWS limits on the total number of
  // audio files.
  while (count > 0 && numAudioSegments++ < maxAudioSegments) {
      [versesUsed,mp3url] = tomp3url(book,c,v,count);
      count -= versesUsed;
      totalVersesUsed += versesUsed;
      retval += '<audio src="' + mp3url + '" />';
      while (versesUsed-- > 0) {
          v++;
          if (v > versesPerChapter[book-1][c-1]) {
             v = 1;
             c++;
          }
      }
  }

  // count is now the number of verses which we omitted

  return [count,totalVersesUsed,retval];
}
