# APIs e Recursos AWS Adicionais para FinOps

## APIs de Cost Management Identificadas

### 1. AWS Cost Anomaly Detection API
- **GetAnomalies**: Recupera anomalias de custo detectadas
- **CreateAnomalyMonitor**: Cria monitores de anomalias
- **Uso**: Detectar picos inesperados de gastos usando ML

### 2. Savings Plans Coverage API
- **GetSavingsPlansCoverage**: Recupera cobertura de Savings Plans
- **Uso**: Verificar quanto do gasto elegível está coberto

### 3. Reserved Instance Utilization API
- **GetReservationUtilization**: Recupera utilização de RIs
- **Uso**: Verificar se RIs estão sendo utilizadas adequadamente

### 4. Cost Optimization Hub API
- **GetRecommendations**: Recupera recomendações consolidadas
- **Uso**: Obter recomendações de múltiplas fontes

## Recursos AWS para Análise

### RDS
- **describe_db_instances**: Listar instâncias RDS
- **CloudWatch Metrics**: DatabaseConnections, CPUUtilization

### EBS Snapshots
- **describe_snapshots**: Listar snapshots
- **Filtrar por data de criação**

### Elastic IPs
- **describe_addresses**: Listar IPs elásticos
- **Verificar associação**

### Load Balancers
- **describe_load_balancers**: Listar ALB/NLB
- **CloudWatch Metrics**: RequestCount, ActiveConnectionCount

### NAT Gateways
- **describe_nat_gateways**: Listar NAT Gateways
- **CloudWatch Metrics**: BytesOutToDestination, BytesOutToSource

### S3 Storage Analytics
- **get_bucket_analytics_configuration**: Análise de storage
- **S3 Intelligent-Tiering**: Recomendações automáticas

### Tags
- **get_cost_and_usage com GroupBy Tags**: Análise por tags
- **Cost Allocation Tags**: Rastreamento por centro de custo
