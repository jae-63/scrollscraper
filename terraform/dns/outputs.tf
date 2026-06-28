output "name_servers" {
  description = "Give these 4 NS records to the adatshalom.net DNS manager (Google Cloud) to delegate the scrollscraper subdomain to Route53"
  value       = aws_route53_zone.scrollscraper.name_servers
}

output "zone_id" {
  description = "Route53 hosted zone ID (needed by future ACM and ALB Terraform)"
  value       = aws_route53_zone.scrollscraper.zone_id
}
