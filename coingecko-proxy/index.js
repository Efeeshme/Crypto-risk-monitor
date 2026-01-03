const express = require("express");
const axios = require("axios");
const cors = require("cors");

const app = express();
app.use(cors());

const BASE = "https://api.coingecko.com/api/v3";

app.get("/coins/list", async (req, res) => {
  try {
    const r = await axios.get(`${BASE}/coins/list`);
    res.json(r.data);
  } catch (e) {
    res.status(500).json({ error: "Coin list fetch failed" });
  }
});

app.get("/coins/markets", async (req, res) => {
  try {
    const r = await axios.get(`${BASE}/coins/markets`, {
      params: {
        vs_currency: "usd",
        ids: req.query.ids,
        price_change_percentage: "1h,24h,7d",
      },
    });
    res.json(r.data);
  } catch (e) {
    res.status(500).json({ error: "Market data fetch failed" });
  }
});

app.listen(3001, () => {
  console.log("✅ CoinGecko proxy running on http://localhost:3001");
});