from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Portfolio, PortfolioAsset
import os
import requests
from openai import OpenAI

# ======================================================
# LANDING
# ======================================================
def landing_view(request):
    return render(request, "public/landing.html")
# ======================================================
# AUTH
# ======================================================
def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            return render(request, "registration/signup.html", {
                "error": "Bu kullanıcı adı zaten alınmış."
            })

        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect("dashboard")

    return render(request, "registration/signup.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")

        return render(request, "registration/login.html", {
            "error": "Kullanıcı adı veya şifre hatalı."
        })

    return render(request, "registration/login.html")


def logout_view(request):
    logout(request)
    return redirect("landing")


# ======================================================
# COINGECKO PROXY
# ======================================================
COIN_ID_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "AVAX": "avalanche-2",
    "ADA": "cardano",
    "DOT": "polkadot",
    "UNI": "uniswap",
    "AAVE": "aave",
    "LINK": "chainlink",
    "XRP": "ripple",
    "BNB": "binancecoin",
    "MATIC": "polygon-ecosystem-token",
    "ARB": "arbitrum",
    "OP": "optimism",
    "INJ": "injective-protocol",
    "TON": "the-open-network",
}

def fetch_market_data(symbol: str):
    """
    symbol: 'BTC' gibi.
    Coingecko 'ids' istediği için symbol -> id map yapıyoruz.
    Bilinmeyen symbol ise None döner (asset eklenir ama market alanları boş kalır).
    """
    coin_id = COIN_ID_MAP.get(symbol.upper())
    if not coin_id:
        return None

    try:
        r = requests.get(
            "http://localhost:3001/coins/markets",
            params={
                "vs_currency": "usd",
                "ids": coin_id,
                "price_change_percentage": "24h,7d"
            },
            timeout=5
        )
        if r.status_code != 200:
            return None

        data = r.json()
        if not isinstance(data, list) or not data:
            return None

        return data[0]
    except Exception as e:
        print("MARKET FETCH ERROR >>>", e)
        return None
# ======================================================
# DASHBOARD
# ======================================================
@login_required
def dashboard(request):
    portfolio = Portfolio.objects.first()
    if not portfolio:
        portfolio = Portfolio.objects.create(total_value_usd=0)

    if request.method == "POST":
        # ✅ HYBRID: dropdown + manual ayrı isimde
        symbol_select = request.POST.get("symbol_select", "").upper().strip()
        symbol_manual = request.POST.get("symbol_manual", "").upper().strip()

        symbol = symbol_manual if symbol_manual else symbol_select

        try:
            value_usd = float(request.POST.get("value_usd", 0))
        except ValueError:
            value_usd = 0

        # hiç symbol gelmediyse ekleme yapma (sessizce dashboard'a dön)
        if not symbol:
            return redirect("dashboard")

        market = fetch_market_data(symbol)

        PortfolioAsset.objects.create(
            portfolio=portfolio,
            symbol=symbol,
            value_usd=value_usd,
            allocation_percent=0,

            # market varsa doldur, yoksa NULL
            price_usd=market.get("current_price") if market else None,
            change_24h=market.get("price_change_percentage_24h_in_currency") if market else None,
            change_7d=market.get("price_change_percentage_7d_in_currency") if market else None,
            market_cap=market.get("market_cap") if market else None,
            volume_24h=market.get("total_volume") if market else None,
        )

        assets = PortfolioAsset.objects.filter(portfolio=portfolio)
        total_value = sum(a.value_usd for a in assets)

        portfolio.total_value_usd = total_value
        portfolio.save()

        for a in assets:
            a.allocation_percent = round((a.value_usd / total_value) * 100, 2) if total_value > 0 else 0
            a.save()

        return redirect("dashboard")

    assets = PortfolioAsset.objects.filter(portfolio=portfolio)

    return render(request, "crmapp/dashboard.html", {
        "portfolio": portfolio,
        "assets": assets,
        "coin_symbols": sorted(COIN_ID_MAP.keys()),
    })


# ======================================================
# AI (TEXT ONLY)
# ======================================================
AI_PROMPT = """
Analyze this crypto portfolio based ONLY on allocation.

Rules:
- ETH/BTC dominance lowers risk
- Too few (3–5) or too many (12+) assets increase risk
- Focus on allocation, not coin names

Write 3–5 clear sentences.
End with ONE concrete improvement suggestion.
"""

def ai_explain_portfolio(assets):
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        assets_text = ""
        for a in assets:
            assets_text += f"- {a.symbol}: %{a.allocation_percent}\n"

        prompt = AI_PROMPT + "\nPortfolio:\n" + assets_text

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    except Exception:
        return "AI analizi şu anda alınamadı."


# ======================================================
# METRICS (SECURITY SCORE)
# ======================================================
def calculate_metrics(assets):
    score = 50
    asset_count = len(assets)

    eth_btc_ratio = sum(
        a.allocation_percent
        for a in assets
        if a.symbol in ["ETH", "BTC"]
    )

    defi_symbols = ["UNI", "AAVE", "COMP", "MKR", "CRV", "INJ", "SNX", "ETHFI"]
    has_defi = any(a.symbol in defi_symbols for a in assets)

    if eth_btc_ratio >= 50:
        score += 30
    elif eth_btc_ratio > 0:
        score += 10
    else:
        score -= 30

    if 3 <= asset_count <= 15:
        score += 20
    else:
        score -= 20

    if has_defi:
        score += 20
    else:
        score -= 30

    score = max(0, min(100, score))

    return {
        "security_score": score,
        "risk_level": "GÜVENLİ" if score >= 70 else "GÜVENSİZ"
    }


# ======================================================
# DETAIL
# ======================================================
@login_required
def detail(request):
    portfolio = Portfolio.objects.filter(user=request.user).first()

    if not portfolio:
        return render(request, "crmapp/detail.html", {
            "portfolio": None,
            "assets": [],
            "ai_explanation": "Portföy bulunamadı.",
            "ai_metrics": {}
        })

    assets = PortfolioAsset.objects.filter(portfolio=portfolio)

    if not assets.exists():
        return render(request, "crmapp/detail.html", {
            "portfolio": portfolio,
            "assets": assets,
            "ai_explanation": "Portföyde henüz varlık yok.",
            "ai_metrics": {}
        })

    ai_text = ai_explain_portfolio(assets)
    ai_metrics = calculate_metrics(assets)

    return render(request, "crmapp/detail.html", {
        "portfolio": portfolio,
        "assets": assets,
        "ai_explanation": ai_text,
        "ai_metrics": ai_metrics
    })


# ======================================================
# DELETE
# ======================================================
@login_required
def delete_asset(request, asset_id):
    asset = PortfolioAsset.objects.get(id=asset_id, portfolio__user=request.user)
    portfolio = asset.portfolio
    asset.delete()

    assets = PortfolioAsset.objects.filter(portfolio=portfolio)
    total_value = sum(a.value_usd for a in assets)

    portfolio.total_value_usd = total_value
    portfolio.save()

    for a in assets:
        a.allocation_percent = round(
            (a.value_usd / total_value) * 100, 2
        ) if total_value > 0 else 0
        a.save()

    return redirect("dashboard")