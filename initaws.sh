
awslocal elasticache create-cache-cluster --cache-cluster-id c1

awslocal rds create-db-instance --db-instance-identifier db1 --db-instance-class c1 --engine postgres --master-username obscure-user --master-user-password obscure-password
