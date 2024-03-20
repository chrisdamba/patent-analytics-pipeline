resource "aws_vpc" "patent_vpc" {
  cidr_block           = "10.16.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "patent_vpc"
  }
}

resource "aws_subnet" "patent_public_subnet" {
  vpc_id                  = aws_vpc.patent_vpc.id
  cidr_block              = "10.16.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "eu-west-2a"

  tags = {
    Name = "patent_public"
  }
}

resource "aws_internet_gateway" "patent_igw" {
  vpc_id = aws_vpc.patent_vpc.id

  tags = {
    Name = "patent_igw"
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
  subnet_id      = aws_subnet.patent_public_subnet.id
  route_table_id = aws_route_table.patent_public_rt.id
}


resource "aws_security_group" "patent_sg" {
  name        = "patent_sg"
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

resource "aws_key_pair" "patent_key" {
  key_name   = "patent_key"
  public_key = file(var.public_key_path)
}

resource "aws_s3_bucket" "raw_patent_data" {
  bucket = var.bucket_name

  tags = {
    Name        = "Patent Analytics Data Bucket"
    Environment = "Dev"
  }
}
