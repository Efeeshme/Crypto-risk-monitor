# crmapp/models.py
from django.contrib.auth.models import User
from django.db import models



class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_value_usd = models.FloatField(default=0)


class PortfolioAsset(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)
    value_usd = models.FloatField()
    allocation_percent = models.FloatField(default=0)

    # 🔹 MARKET DATA (CoinGecko)
    price_usd = models.FloatField(null=True, blank=True)
    change_1h = models.FloatField(null=True, blank=True)
    change_24h = models.FloatField(null=True, blank=True)
    change_7d = models.FloatField(null=True, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    volume_24h = models.BigIntegerField(null=True, blank=True)





class RiskMetric(models.Model):
    asset = models.ForeignKey(
        PortfolioAsset,
        related_name="metrics",
        on_delete=models.CASCADE
    )
    volatility = models.FloatField()
    asset_risk_score = models.IntegerField()
    explanation = models.TextField()


