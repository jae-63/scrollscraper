resource "aws_route53_zone" "scrollscraper" {
  name = "scrollscraper.adatshalom.net"
}

resource "aws_route53_record" "a" {
  zone_id = aws_route53_zone.scrollscraper.zone_id
  name    = "scrollscraper.adatshalom.net"
  type    = "A"
  ttl     = 300
  records = [var.ec2_ip]
}
