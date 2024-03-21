data "aws_availability_zones" "available" {
  filter {
    name   = "group-name"
    values = [var.region]
  }
}

locals {
  az_names = sort(data.aws_availability_zones.available.names)
}

resource "aws_vpc" "patent_vpc" {
  cidr_block           = "10.16.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "patent_vpc"
  }
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  cidr_block              = var.public_subnet_cidrs[count.index]
  vpc_id                  = aws_vpc.patent_vpc.id
  map_public_ip_on_launch = true
  availability_zone       = count.index % 2 == 0 ? local.az_names[0] : local.az_names[1]
  tags = {
    Name = "patent-mwaa-${var.environment_name}-public-subnet-${count.index}"
  }
}

resource "aws_subnet" "private" {
  count                   = length(var.private_subnet_cidrs)
  cidr_block              = var.private_subnet_cidrs[count.index]
  vpc_id                  = aws_vpc.patent_vpc.id
  map_public_ip_on_launch = false
  availability_zone       = count.index % 2 == 0 ? local.az_names[0] : local.az_names[1]
  tags = {
    Name = "patent-mwaa-${var.environment_name}-private-subnet-${count.index}"
  }
}

resource "aws_eip" "patent_eip" {
  count  = length(var.public_subnet_cidrs)
  domain = "vpc"
  tags = {
    Name = "patent-mwaa-${var.environment_name}-eip-${count.index}"
  }
}

resource "aws_nat_gateway" "patent_nat_gateway" {
  count         = length(var.public_subnet_cidrs)
  allocation_id = aws_eip.patent_eip[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  tags = {
    Name = "patent-mwaa-${var.environment_name}-nat-gateway-${count.index}"
  }
}

resource "aws_internet_gateway" "patent_igw" {
  vpc_id = aws_vpc.patent_vpc.id

  tags = {
    Name = "patent-mwaa-${var.environment_name}-internet-gateway"
  }
}

resource "aws_route_table" "patent_public_rt" {
  vpc_id = aws_vpc.patent_vpc.id

  tags = {
    Name = "patent_public_rt"
  }
}

resource "aws_route" "default_route" {
  route_table_id         = aws_route_table.patent_public_rt.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.patent_igw.id
}

resource "aws_route_table_association" "patent_public_assoc" {
  count  = length(var.public_subnet_cidrs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.patent_public_rt[count.index].id
}

resource "aws_route_table" "patent_private_rt" {
  count  = length(aws_nat_gateway.patent_nat_gateway)
  vpc_id = aws_vpc.patent_vpc.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.patent_nat_gateway[count.index].id
  }
  tags = {
    Name = "patent-mwaa-${var.environment_name}-private-routes-a"
  }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  route_table_id = aws_route_table.patent_private_rt[count.index].id
  subnet_id      = aws_subnet.private[count.index].id
}

resource "aws_security_group" "patent_mwaa_sg" {
  vpc_id = aws_vpc.patent_vpc.id
  name   = "patent-mwaa-${var.environment_name}-no-ingress-sg"
  tags = {
    Name = "patent-mwaa-${var.environment_name}-no-ingress-sg"
  }
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }
  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = [
      "0.0.0.0/0"
    ]
  }
}

resource "aws_security_group" "patent_sg" {
  name   = "patent_sg"
  vpc_id = aws_vpc.patent_vpc.id

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [join("/", [var.my_ip, "32"])]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
