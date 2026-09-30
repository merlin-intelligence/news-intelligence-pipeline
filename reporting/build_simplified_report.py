# -*- coding: utf-8 -*-
"""
build_simplified_report.py

Generates the simplified, executive De-Dollarization News Ranking HTML report:
- Incorporates curated, clean executive summaries and specific monetary mechanisms for the Top 20 priority news.
- Skips theoretical methodology and onto-semantic pipeline sections.
- Focuses directly on the 12-Bucket Category Overview, Top 20 Priority Intelligence Cards (chronological order), and Following 50 Ranked News Table (Ranks 21-70).
- Employs Equi-Weighted Multi-Anchor Concept Immersion and Composite Eigenmind Singularity scoring.
- Resolves publisher links directly and includes country geotags with score intensity gradients.
"""

import os
import sys
import io
import html
import glob
import re
import pandas as pd
import numpy as np
import shutil
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

BUCKET_TAXONOMY = [
    {"id": "1.1", "name": "Foreign Exchange Reserve Composition (IMF COFER)", "desc": "Tracking USD share trajectory, RMB/Euro reserve expansion, and non-traditional currency asset allocations."},
    {"id": "1.2", "name": "International Debt & Sovereign Bond Denomination", "desc": "Compression of USD debt share, Panda bond debuts (RMB), and Euro sovereign issuances."},
    {"id": "1.3", "name": "Global Trade Finance & Payments Network (SWIFT & BIS)", "desc": "SWIFT messaging share shifts, OTC FX turnover contraction, and cross-border bank loan currency shares."},
    {"id": "1.4", "name": "Treasury Convenience Yield & Swap Spread Compression", "desc": "Negative convenience yield, deeply negative swap spreads, and sovereign safe-haven premium erosion."},
    {"id": "1.5", "name": "Trade Policy Shocks & Tariff Threshold Dynamics", "desc": "Tariff threshold switching dynamics and risk-off asset appreciation outside the U.S. dollar."},
    {"id": "2.1", "name": "Central Bank Physical Gold Accumulation", "desc": "Record official gold purchases, un-freezable conflict hedging, and gold surpassing Treasuries in reserves."},
    {"id": "2.2", "name": "Alternative Clearing Rails (CIPS & Project mBridge)", "desc": "Cross-Border Interbank Payment System volume surges, non-SWIFT clearing, and multi-CBDC platforms."},
    {"id": "2.3", "name": "Commodity Invoicing & 'Petroyuan' Realignment", "desc": "1974 Saudi petrodollar expiry, non-dollar crude/LNG pricing, and Hormuz transit fee settlement."},
    {"id": "2.4", "name": "Non-USD Stablecoins & Digital Sovereign Assets", "desc": "Non-USD stablecoins growth, digital yuan/euro P2P corridors, and tokenized commercial deposit disintermediation."},
    {"id": "2.5", "name": "Deviations from Covered Interest Parity (CIP) & Auction Thinning", "desc": "CIP breakdown, rising USD borrowing friction, and diminishing indirect bidder allocations in Treasury auctions."},
    {"id": "2.6", "name": "Bilateral Swap Networks & Green RMB Bonds", "desc": "Bilateral central bank currency swap facilities and green RMB bond benchmarks providing non-USD safe assets."},
    {"id": "2.7", "name": "Institutional Credibility & Central Bank Governance Cues", "desc": "Federal Reserve independence cues, policy interference risks, and central bank governance trust."}
]

BUCKET_DESCRIPTORS = {
    "1.1": "IMF COFER foreign exchange reserve composition dollar share decline renminbi euro diversification reserve assets non-traditional currencies",
    "1.2": "international debt sovereign bond denomination panda bonds euro-denominated debt issuance cross-border loans non-USD debt",
    "1.3": "global trade finance payments network SWIFT payment share BIS triennial survey OTC foreign exchange turnover correspondent banking",
    "1.4": "treasury convenience yield swap spread compression U.S. sovereign debt premium interest rate swap spreads G10 sovereign yields",
    "1.5": "trade policy shocks tariff threshold dynamics protectionism trade war invoicing switch safe-haven risk-off appreciation",
    "2.1": "central bank physical gold accumulation official gold reserves unfreezable hedge conflict risk gold surpassing treasuries",
    "2.2": "alternative clearing rails CIPS project mBridge cross-border interbank payment system multi-CBDC wCBDC non-SWIFT clearing",
    "2.3": "commodity invoicing petroyuan petrodollar agreement saudi arabia crude oil LNG trade settlement strait of hormuz transit fees",
    "2.4": "non-USD stablecoins digital sovereign assets digital yuan digital euro tokenized bank deposits cross-border P2P payments",
    "2.5": "covered interest parity CIP deviations treasury auction thinning indirect bidder allocations dollar liquidity borrowing premium",
    "2.6": "bilateral currency swap networks green RMB bonds central bank swap facility liquidity backstop ESG safe asset",
    "2.7": "institutional credibility central bank governance federal reserve independence policy interference monetary authority trust"
}

# --- Precise Curated Executive Summaries & Specific Monetary Mechanisms ---
EXECUTIVE_CATALOG = [
    {
        "keywords": ["govt eyes first sovereign dollar bond", "targets $500m-$1b", "the business standard"],
        "summary": "Emerging market sovereign debt authorities are weighing inaugural foreign currency bond issuances, evaluating external financing options between traditional dollar debt and alternative onshore renminbi Panda bonds to mitigate external debt servicing vulnerabilities.",
        "mechanism": "<b>International Debt & Sovereign Bond Denomination (Bucket 1.2):</b> Emerging market sovereign balance sheets evaluate currency denomination trade-offs between traditional USD debt and renminbi Panda bonds to optimize sovereign borrowing costs and insulate against dollar volatility."
    },
    {
        "keywords": ["us tech bond bonanza", "raise european borrowing costs", "ecb analysts"],
        "summary": "European Central Bank economists warn that a massive wave of bond sales by U.S. technology giants is crowding out demand for European sovereign debt, driving up borrowing costs across the euro area as private corporate issuers compete directly with G10 sovereign treasuries.",
        "mechanism": "<b>International Debt Denomination & Sovereign Crowding Out (Bucket 1.2):</b> High-yield U.S. corporate debt issuance absorbs global fixed-income duration appetite, compressing foreign absorption of sovereign paper and shifting debt denomination dynamics."
    },
    {
        "keywords": ["china just broke its own gold-buying record", "pboc-gold-reserves-august-2026", "goldsilver"],
        "summary": "The People's Bank of China registered its 22nd consecutive month of physical gold reserve expansion, marking the largest consecutive monthly accumulation streak since 2023. China's official gold holdings reached 2,366 metric tons, reflecting a deliberate, long-term de-dollarization strategy.",
        "mechanism": "<b>Sovereign Reserve Composition & Gold Hedging (Bucket 2.1):</b> Systematic balance-sheet replacement of U.S. Treasury assets with physical bullion, securing monetary reserves against potential foreign exchange asset freezes."
    },
    {
        "keywords": ["gold sub-$4300", "western bond yields soar", "bullionvault"],
        "summary": "As Western long-term sovereign bond yields surge amid persistent fiscal deficits, physical gold consolidates near historic highs around $4,300/oz. Concurrently, the People's Bank of China continues expanding its physical bullion reserves, cementing gold as the primary non-Western sovereign reserve anchor.",
        "mechanism": "<b>Central Bank Physical Gold Accumulation (Bucket 2.1):</b> Reallocation of official sovereign reserves from depreciating, sanction-vulnerable Western sovereign paper into physically vaulted, un-freezable gold bullion."
    },
    {
        "keywords": ["jonathan levin warns of blurred lines", "levin-warns-blurred-monetary-policy-lines", "blurred lines in monetary policy"],
        "summary": "Financial analyst Jonathan Levin cautions that skyrocketing U.S. government debt is eroding the institutional boundary between central banks and finance ministries, threatening central bank independence and creating risks of fiscal dominance and debt monetization.",
        "mechanism": "<b>Institutional Credibility & Central Bank Governance Cues (Bucket 2.7):</b> Rising risks of fiscal dominance undermine global confidence in the Federal Reserve's institutional autonomy, eroding the dollar's institutional credibility premium."
    },
    {
        "keywords": ["oil trade’s shift towards a currency-agnostic future", "currency-agnostic future", "et energyworld"],
        "summary": "Global crude oil trade is transitioning toward a currency-agnostic settlement regime as major exporters and importers bypass the traditional petrodollar architecture, settling energy cargoes in local currencies, renminbi, and dirhams.",
        "mechanism": "<b>Commodity Invoicing & 'Petroyuan' Realignment (Bucket 2.3):</b> Structural transition away from mandatory dollar energy pricing, allowing strategic energy trade to clear in sovereign national currencies."
    },
    {
        "keywords": ["payment, currency ties to boost brics", "ties to boost brics", "china daily"],
        "summary": "Following the 18th BRICS Summit in New Delhi, member states are intensifying cooperation to implement local currency payment systems, interlink domestic instant clearing mechanisms, and reduce transaction reliance on Western financial rails and SWIFT messaging.",
        "mechanism": "<b>Alternative Clearing Rails & Non-SWIFT Messaging (Bucket 2.2):</b> Multilateral integration of national payment switches and clearing rails creates autonomous trade corridors resilient against extraterritorial sanctions."
    },
    {
        "keywords": ["dollar's declining reserve share reflects few countries", "ny fed says", "scoreboard might be mislea"],
        "summary": "New research from the Federal Reserve Bank of New York argues that the gradual decline in the U.S. dollar's share of global reserves is concentrated in a select group of geopolitical non-aligned and surplus economies, rather than representing an immediate broad-based institutional abandonment of the currency.",
        "mechanism": "<b>Foreign Exchange Reserve Composition & Concentration Dynamics (Bucket 1.1):</b> Structural divergence in sovereign reserve policy, where active de-dollarization is heavily concentrated among geopolitical surplus powers reallocating into gold and bilateral currencies."
    },
    {
        "keywords": ["malaysia agrees in principle to us$100mil currency swap", "currency swap with maldives", "maldives thanks malaysia"],
        "summary": "Malaysia and the Maldives reached an agreement in principle on a $100 million bilateral currency swap facility, providing direct regional liquidity and foreign exchange stability while bypassing intermediate conversions through the U.S. dollar.",
        "mechanism": "<b>Bilateral Swap Networks & Regional Liquidity Backstops (Bucket 2.6):</b> Direct central bank currency swap arrangements insulate small and medium emerging economies from dollar liquidity squeezes."
    },
    {
        "keywords": ["the world economy is becoming wary of the u.s.", "inquirer.com", "america-debt-dollar-sanctions-gold"],
        "summary": "International investors and foreign monetary authorities express mounting unease over unsustainable U.S. debt trajectories, escalating tariff regimes, and the aggressive weaponization of sanctions, accelerating capital allocations into physical gold and non-dollar sovereign debt.",
        "mechanism": "<b>Sovereign Risk-Off Reallocation & Dollar Safe-Haven Erosion (Bucket 2.1):</b> Escalating U.S. fiscal trajectory and policy unpredictability degrade the traditional risk-free premium of U.S. Treasuries, driving foreign balance sheets into physical bullion."
    },
    {
        "keywords": ["us-iran conflict reignites as hedge funds push crude", "hedge funds push crude oil"],
        "summary": "Military confrontations between the U.S. and Iran have reignited energy risk premiums, driving hedge funds to establish large bullish bets on crude oil and highlighting the vulnerability of Strait of Hormuz oil transit routes to geopolitical dislocation.",
        "mechanism": "<b>Commodity Invoicing & Geopolitical Risk Hedging (Bucket 2.3):</b> Geopolitical escalation in primary energy export corridors incentivizes energy importers to secure direct bilateral supply agreements settled outside Western clearing channels."
    },
    {
        "keywords": ["bank of maharashtra's usd 500m overseas bonds", "bank of maharashtra"],
        "summary": "Bank of Maharashtra's $500 million debut overseas bond issuance saw nearly 3x oversubscription, reflecting international investor appetite for emerging market financial institution paper backed by Reserve Bank of India foreign exchange swap mechanisms.",
        "mechanism": "<b>International Debt & Sovereign Bond Denomination (Bucket 1.2):</b> Emerging market institutions utilize overseas bond markets and central bank swap facilities to access diversified foreign capital while managing FX risk."
    },
    {
        "keywords": ["china holds 2,366 tons of gold", "cointribune", "2,366 tons of gold as yuan ambitions grow"],
        "summary": "China's official gold reserves reached 2,366 metric tons following 22 consecutive months of steady purchases, illustrating how Beijing is anchoring the physical foundations of its currency internationalization strategy with un-encumbered hard assets.",
        "mechanism": "<b>Central Bank Physical Gold Accumulation (Bucket 2.1):</b> Long-term institutional re-anchoring of sovereign reserve balance sheets with physical bullion to support credibility in a multipolar currency regime."
    },
    {
        "keywords": ["a big moment for the digital euro", "digital euro as a cbdc", "digital euro"],
        "summary": "The European Central Bank advances the digital euro project toward implementation, creating a sovereign European retail and wholesale digital payment rail intended to safeguard monetary sovereignty, reduce reliance on US-based payment networks, and strengthen the euro's international role.",
        "mechanism": "<b>Non-USD Digital Sovereign Assets & Monetary Autonomy (Bucket 2.4):</b> Sovereign CBDC issuance provides a native digital clearing rail that eliminates dependency on foreign card schemes and private digital currencies."
    },
    {
        "keywords": ["top 10 countries with the biggest forex reserves", "biggest forex reserves"],
        "summary": "An analysis of the world's largest sovereign foreign exchange reserve holders, highlighting how top-tier reserve managers (China, Japan, Switzerland, India, Russia, Saudi Arabia) are systematically diversifying reserve asset mixes into gold, regional currencies, and non-dollar assets.",
        "mechanism": "<b>Foreign Exchange Reserve Composition (Bucket 1.1):</b> Global reserve concentration trends show major surplus sovereigns diversifying official assets to reduce vulnerability to single-currency concentration risks."
    },
    {
        "keywords": ["don’t panic about a us bond market selloff", "dont-panic-about-bond-market-selloff", "morningstar"],
        "summary": "Fixed income analysis assesses rising U.S. Treasury yields, with the 30-year bond reaching 19-year highs at 5.3%, evaluating whether elevated yields reflect cyclical growth expectations or structural term premium expansion driven by heavy fiscal issuance.",
        "mechanism": "<b>Treasury Convenience Yield & Swap Spread Compression (Bucket 1.4):</b> Elevation of long-term sovereign bond yields and persistent negative swap spreads signal structural degradation of the Treasury convenience premium."
    },
    {
        "keywords": ["rmb use expands in africa amid growing financial connectivity", "rmb use expands in africa", "xinhua"],
        "summary": "Cross-border renminbi usage is accelerating across African economies, supported by bilateral central bank swap agreements, direct clearing hubs, and growing local-currency settlement for infrastructure, raw materials, and manufactured imports.",
        "mechanism": "<b>Bilateral Swap Networks & RMB Internationalization (Bucket 2.6):</b> Bilateral central bank liquidity facilities and offshore clearing corridors facilitate direct bilateral trade clearing without intermediate USD conversion."
    },
    {
        "keywords": ["tokenized gold trading tops $126b", "wintermute enters market", "coinmarketcap"],
        "summary": "Institutional adoption of tokenized physical gold has surged past $126 billion in trading volume as institutional market makers enter the sector, providing high-liquidity, 24/7 on-chain access to physical bullion as a liquid alternative to traditional dollar cash equivalents.",
        "mechanism": "<b>Digital Sovereign Assets & Tokenized Gold Settlement (Bucket 2.1 / 2.4):</b> Distributed ledger tokenization allows physical gold to function with the velocity and transaction efficiency of cash, displacing USD-pegged stablecoins in cross-border collateral management."
    },
    {
        "keywords": ["opinion: central bank independence should have a limit", "central bank independence limit", "the globe and mail"],
        "summary": "Macroeconomic debate on institutional central bank governance, examining the balance between democratic accountability and monetary policy independence as rising fiscal debt burdens increase pressure for monetary-fiscal coordination.",
        "mechanism": "<b>Institutional Credibility & Central Bank Governance Cues (Bucket 2.7):</b> Public debates over central bank independence signal potential risks of fiscal dominance, weakening foreign institutional confidence in long-term monetary stability."
    },
    {
        "keywords": ["brics builds an alternative path for global payments", "new delhi declaration", "dailynews.co.tz"],
        "summary": "The 18th BRICS Summit in New Delhi formalized concrete frameworks for alternative payment architecture, including decentralized cross-border messaging protocols, local currency bilateral settlement, and clearing mechanisms independent of Western jurisdiction.",
        "mechanism": "<b>Global Trade Finance & Alternative Messaging Networks (Bucket 1.3 / 2.2):</b> Structural engineering of redundant financial messaging and cross-border settlement channels independent of SWIFT and CHIPS."
    },
    {
        "keywords": ["gold at $15,000: fantasy, forecast - or warning?", "kitco", "gold-15000-fantasy-forecast-or-warning"],
        "summary": "Market analysts and monetary historians examine extreme upside projections for gold prices, arguing that unprecedented valuation surges reflect sovereign balance-sheet debasement, runaway fiscal deficits, and the structural re-anchoring of the global monetary system.",
        "mechanism": "<b>Monetary System Re-anchoring & Physical Bullion Valuation (Bucket 2.1):</b> Parabolic bullion price projections reflect fundamental market reassessments of fiat currency purchasing power amid sovereign debt compounding."
    },
    {
        "keywords": ["the weekly spread: what shaped yields and the dollar this week", "the weekly spread", "tradingview"],
        "summary": "Fixed income analysis tracking the sharp rise in 2-year U.S. Treasury yields to 4.75% alongside steepening 10-year and 30-year yields, driven by monetary policy uncertainty and sovereign debt issuance absorption frictions.",
        "mechanism": "<b>Treasury Convenience Yield & Swap Spread Compression (Bucket 1.4):</b> Volatility in Treasury term premiums and swap spreads reflects diminishing foreign absorption capacity for expanding U.S. sovereign debt issuance."
    },
    {
        "keywords": ["why unrest in the strait of hormuz is leading to rising oil", "abcnews.com", "unrest in the strait of hormuz"],
        "summary": "Maritime tensions and military strikes in the Strait of Hormuz drove crude oil prices sharply higher, demonstrating the fragility of international energy transit and reinforcing efforts by Asian importers to bypass vulnerable dollar-denominated shipping chokepoints.",
        "mechanism": "<b>Commodity Invoicing & Strategic Energy Chokepoint Transit (Bucket 2.3):</b> Energy security threats accelerate direct bilateral energy supply pacts settled outside traditional dollar maritime trade corridors."
    },
    {
        "keywords": ["the hormuz paradox: how the crisis is reshaping", "russian council", "the-hormuz-paradox"],
        "summary": "Strategic analysis of Persian Gulf maritime security detailing how regional conflict is permanently redirecting energy flows toward overland Eurasian pipelines and non-dollar bilateral settlement networks, reducing the strategic leverage of the U.S. Navy and petrodollar.",
        "mechanism": "<b>Commodity Invoicing & Geopolitical Energy Realignment (Bucket 2.3):</b> Physical rerouting of hydrocarbon flows diminishes petrodollar transaction velocity, establishing local-currency Eurasian trade loops."
    },
    {
        "keywords": ["the truth behind de-dollarisation", "daily observer", "replacing us dollar for other currencies"],
        "summary": "A comprehensive structural overview of global de-dollarization drivers, outlining how trade settlement diversification, multi-currency reserve holding, and alternative cross-border telecommunications networks are gradually eroding the dollar's postwar dominance.",
        "mechanism": "<b>Multilateral Reserve & Trade Diversification (Bucket 1.1):</b> Coordinated reallocation of sovereign reserves, trade invoicing, and clearing channels across a decentralized, multipolar currency basket."
    },
    {
        "keywords": ["china increased gold reserves to 76.73 million ounces", "ua.news", "kitai-zbilshiv-zoloti-rezervi"],
        "summary": "Official reserve disclosure confirms China expanded its physical gold holdings to 76.73 million ounces in August 2026, marking 22 months of uninterrupted additions and representing its largest single-month purchase volume since late 2024.",
        "mechanism": "<b>Central Bank Physical Gold Accumulation (Bucket 2.1):</b> Relentless sovereign bullion accumulation reduces official balance-sheet vulnerability to Western asset freezing orders."
    },
    {
        "keywords": ["bitcoin’s gold correlation hits 50%", "safe-haven edge", "bitget"],
        "summary": "Quantitative correlation between Bitcoin and physical gold reached 50% during recent geopolitical escalations, indicating that digital non-state safe assets are increasingly traded as sovereign debasement hedges alongside physical precious metals.",
        "mechanism": "<b>Trade Policy Shocks & Tariff Threshold Dynamics (Bucket 1.5):</b> Investors seek non-sovereign monetary alternatives outside the reach of capital controls and tariff regimes during geopolitical conflict."
    },
    {
        "keywords": ["2026 policy address | the quota for rmb business funding", "quota for rmb business funding arrangements is expanded to 500 billion", "longbridge"],
        "summary": "The Hong Kong Monetary Authority expanded its RMB Business Facility quota to 500 billion yuan and extended tenors to 3 years, strengthening Hong Kong's role as the premier global offshore renminbi clearing hub and liquidity provider.",
        "mechanism": "<b>Bilateral Swap Networks & Offshore RMB Liquidity (Bucket 2.6):</b> Deepening offshore RMB liquidity backstops provides institutional market participants with the liquidity depth necessary to conduct large-scale non-dollar trade and financial settlement."
    },
    {
        "keywords": ["us 20-year bond auction just had its worst showing ever", "protos.com", "worst 20-year bond auction"],
        "summary": "The U.S. Treasury's September 20-year bond auction experienced historic demand degradation, with primary dealers forced to absorb an unusually large share as foreign indirect bidder participation declined sharply, causing a substantial auction tail.",
        "mechanism": "<b>Deviations from CIP & Treasury Auction Thinning (Bucket 2.5):</b> Diminishing foreign indirect bidder participation in long-duration Treasury auctions demonstrates structural thinning of international demand for expanding U.S. sovereign debt."
    },
    {
        "keywords": ["us dollar safe-haven status", "de-dollarization explained for traders"],
        "summary": "Market strategists analyze how the U.S. dollar's historic safe-haven status is evolving as structural de-dollarization forces, massive U.S. debt issuance, and geopolitical fragmentation create competing safe-haven assets, including gold, swiss francs, and sovereign local-currency debt instruments.",
        "mechanism": "<b>Safe-Haven Substitution & Reserve Diversification (Bucket 1.1):</b> Institutional investors and sovereign wealth funds diversify risk-off allocations across a broader basket of non-dollar liquid assets."
    },
    {
        "keywords": ["gold allocations rise as central banks accelerate", "yuan-led alternative order"],
        "summary": "Global central banks are aggressively expanding their official gold allocations while paring back U.S. Treasury holdings to protect sovereign foreign exchange reserves against geopolitical sanctions and financial weaponization. Simultaneously, Beijing is accelerating bilateral yuan-clearing mechanisms across the Global South to build a resilient, non-dollar reserve order.",
        "mechanism": "<b>Sovereign Reserve Composition & Gold Substitution (Bucket 1.1):</b> Direct rebalancing of official reserves from USD-denominated sovereign debt into physically vaulted bullion, structural compression of global dollar reserve share, and expansion of bilateral non-Western reserve assets."
    },
    {
        "keywords": ["rise of non-usd stablecoins", "coingecko"],
        "summary": "Analysis of the rapid market expansion of non-USD stablecoins (pegged to the euro, dirham, yen, and Singapore dollar) on public and permissioned blockchains. These digital assets facilitate direct cross-border corporate payments, reducing reliance on USD-pegged tokens and intermediate foreign exchange conversion rails.",
        "mechanism": "<b>Non-USD Stablecoins & On-Chain Settlement (Bucket 2.4):</b> Expansion of multi-currency stablecoins enables programmable, atomic settlement across distributed ledgers without requiring intermediate USD clearing rails."
    },
    {
        "keywords": ["dollar hegemony remains intact", "reserve rebalancing has begun"],
        "summary": "International central bank survey data signals the first coordinated reduction in official U.S. dollar allocations in three years. Monetary authorities are reallocating excess reserves into physical gold bullion and euro-denominated sovereign debt, marking an active shift toward multi-currency reserve portfolios.",
        "mechanism": "<b>Foreign Exchange Reserve Composition (Bucket 1.1):</b> Official rebalancing of sovereign foreign exchange holdings away from U.S. dollar paper toward gold and non-dollar G10 sovereign paper."
    },
    {
        "keywords": ["u.s. treasury to auction $58 billion", "investinglive"],
        "summary": "The U.S. Treasury conducted a $58 billion 3-year note auction amid heightened focus on primary dealer absorption capacity and foreign indirect bidder demand. The auction metrics provide key insights into foreign institutional appetite for newly issued U.S. sovereign debt.",
        "mechanism": "<b>Treasury Auction Thinning & Bidder Demand (Bucket 2.5):</b> Monitoring indirect bidder participation rates and primary dealer absorption capacity to evaluate international appetite for absorbing massive U.S. fiscal debt issuance."
    },
    {
        "keywords": ["trump’s liberation day tariffs", "liberation day tariffs"],
        "summary": "Significant tariff announcements and protectionist trade policy measures triggered widespread risk-off liquidations across global asset markets, accelerating geopolitical fragmentation and motivating trade counterparties to explore bilateral non-dollar invoicing to circumvent tariff and trade restrictions.",
        "mechanism": "<b>Trade Policy Shocks & Tariff Threshold Dynamics (Bucket 1.5):</b> Aggressive tariff implementations act as tipping points that incentivize trade partners to establish non-dollar invoicing corridors and alternative bilateral settlement structures."
    },
    {
        "keywords": ["china, mongolia renew bilateral currency swap", "mongolia renew bilateral currency swap"],
        "summary": "The People's Bank of China and the Bank of Mongolia renewed their bilateral currency swap agreement valued at 15 billion yuan ($2.1 billion) for three years. The agreement provides liquidity backstops for bilateral trade settlement, mining exports, and financial stability without intermediate dollar conversion.",
        "mechanism": "<b>Bilateral Currency Swap Networks (Bucket 2.6):</b> Central bank bilateral swap agreements establish direct local-currency liquidity facilities, bypassing traditional dollar correspondent clearing networks."
    },
    {
        "keywords": ["world gold council said 45% of central banks plan", "bitget"],
        "summary": "The World Gold Council's official survey reveals that a record 45% of global central banks intend to increase their physical gold reserves over the next 12 months. Central bank governors cite asset preservation, inflation hedging, and insulation from geopolitical sanctions as the primary catalysts.",
        "mechanism": "<b>Central Bank Physical Gold Accumulation (Bucket 2.1):</b> Accelerating accumulation of un-freezable, physically vaulted gold reserves as sovereign balance sheets seek immunity from Western financial sanctions."
    },
    {
        "keywords": ["china urges swift reopening of strait of hormuz", "bitcoin for transit fees"],
        "summary": "Maritime disruptions in the Strait of Hormuz prompted Iranian authorities and maritime shippers to explore alternative digital and sovereign payment channels for canal transit fees, underscoring how geopolitical chokepoints accelerate non-traditional and non-dollar trade settlement.",
        "mechanism": "<b>Commodity Invoicing & Geopolitical Settlement (Bucket 2.3):</b> Strategic maritime friction points accelerating the adoption of alternative, non-dollar settlement mechanisms for energy transit and shipping fees."
    },
    {
        "keywords": ["the panda bonds: how china uses assets", "south china morning post"],
        "summary": "Foreign sovereigns and multinational corporations are issuing record volumes of Panda bonds (onshore renminbi-denominated debt in China). The market expansion provides global issuers with attractive funding costs while accelerating the internationalization of renminbi-denominated sovereign debt.",
        "mechanism": "<b>International Debt Denomination & Panda Bonds (Bucket 1.2):</b> Expansion of onshore RMB-denominated sovereign debt markets diminishes the global dominance of USD-denominated sovereign bond issuances."
    },
    {
        "keywords": ["what would happen if the u.s. dollar lost its reserve", "marketplace.org"],
        "summary": "Economists and market historians evaluate the structural consequences of declining dollar hegemony, projecting structural increases in long-term U.S. borrowing costs, persistent import inflation, and the necessity of structural fiscal adjustments as global central banks diversify their official foreign exchange reserves.",
        "mechanism": "<b>Reserve Currency Hegemony & Borrowing Costs (Bucket 1.1):</b> Erosion of the dollar's 'exorbitant privilege' elevates Treasury yield term premiums and diminishes foreign absorption of expanding U.S. fiscal deficits."
    },
    {
        "keywords": ["how swift is adapting to the changing payment ecosystem", "deutsche bank"],
        "summary": "SWIFT is re-engineering its core messaging infrastructure to interlink central bank digital currencies (CBDCs), tokenized assets, and instant payment systems across jurisdictions, seeking to maintain its position as the global communications standard amid rising alternative clearing rails.",
        "mechanism": "<b>Payment Messaging Network Interoperability (Bucket 1.3):</b> Upgrading traditional messaging standards (ISO 20022) to retain global network effects and interoperability against sovereign non-SWIFT financial channels."
    },
    {
        "keywords": ["digital yuan will be centerpiece", "paymentsjournal"],
        "summary": "Financial technology analysis detailing how the People's Bank of China is integrating the digital yuan (e-CNY) with commercial banks and regional clearing platforms, establishing an end-to-end sovereign digital payment architecture for global trade and retail settlement.",
        "mechanism": "<b>Alternative Clearing Rails & Digital Currency Infrastructure (Bucket 2.2):</b> Sovereign central bank digital currency infrastructure deployed as an alternative clearing architecture alongside CIPS."
    },
    {
        "keywords": ["china develops digital payments system to challenge us dollar", "crypto briefing"],
        "summary": "China is advancing the cross-border rollout of the digital yuan alongside multilateral CBDC platforms, enabling direct peer-to-peer central bank settlement that eliminates reliance on U.S. correspondent banking rails.",
        "mechanism": "<b>Non-USD Digital Assets & CBDC Disintermediation (Bucket 2.4):</b> Direct multi-CBDC liquidity hubs replace traditional correspondent banking tiers with real-time gross settlement across central bank balance sheets."
    },
    {
        "keywords": ["the u.s. dollar is the world’s reserve currency. why does that matter", "peter g. peterson foundation"],
        "summary": "Policy research exploring the economic benefits and vulnerabilities of the dollar's global reserve role, analyzing how foreign demand for U.S. Treasuries lowers domestic borrowing costs while exposing the domestic economy to foreign balance sheet diversification.",
        "mechanism": "<b>Foreign Exchange Reserve Hegemony (Bucket 1.1):</b> Analysis of macroeconomic capital flows and sovereign reserve holdings underpinning U.S. sovereign debt sustainability."
    },
    {
        "keywords": ["global safe assets and their convenience yields"],
        "summary": "European Central Bank working paper analyzing the supply, demand, and convenience yield dynamics of global safe assets. The research highlights the scarcity of non-U.S. sovereign safe assets and the compression of convenience yields across global capital markets.",
        "mechanism": "<b>Treasury Convenience Yield & Swap Spread Compression (Bucket 1.4):</b> Quantitative measurement of safe-haven convenience yield premiums and interest rate swap spread dynamics between U.S. Treasuries and European sovereign paper."
    },
    {
        "keywords": ["fed chair warsh tests central bank independence", "legis1"],
        "summary": "Institutional governance analysis examining executive branch interactions with Federal Reserve leadership, evaluating the risks of political pressure on monetary policy decisions and its impact on international central bank confidence in the U.S. financial system.",
        "mechanism": "<b>Institutional Credibility & Central Bank Governance (Bucket 2.7):</b> Perceptions of central bank independence and institutional governance as critical pillars maintaining foreign confidence in the reserve currency."
    },
    {
        "keywords": ["mncs drive expansion of china's cips", "china daily global edition"],
        "summary": "Multinational corporations across Asia and Europe are increasingly connecting to China's Cross-Border Interbank Payment System (CIPS) for corporate trade invoicing and regional treasury management, mitigating sanction exposures and currency conversion costs.",
        "mechanism": "<b>Alternative Clearing Rails & Non-SWIFT Messaging (Bucket 2.2):</b> Expansion of CIPS direct participants establishes an independent RMB clearing architecture, decoupling international trade settlement from CHIPS and SWIFT rails."
    },
    {
        "keywords": ["the international role of the euro, june 2026", "international role of the euro"],
        "summary": "The European Central Bank's 2026 comprehensive report on the international role of the euro reveals resilient euro invoicing in global trade and expanding usage in cross-border green sovereign bond issuances, positioning the currency as a key pillar in a multipolar monetary system.",
        "mechanism": "<b>Reserve Currency Multipolarity & Euro Invoicing (Bucket 1.1):</b> Structural expansion of euro-denominated trade invoicing and official reserve allocations providing diversification outside the dollar zone."
    },
    {
        "keywords": ["petrodollar collapse: iran-yuan oil trade", "coin gabbar"],
        "summary": "Iranian crude oil shipments to Chinese refineries are settled almost exclusively in renminbi using non-dollar accounts and non-SWIFT communication channels, solidifying an energy settlement ecosystem outside the traditional U.S. petrodollar architecture.",
        "mechanism": "<b>Commodity Invoicing & 'Petroyuan' Realignment (Bucket 2.3):</b> Structural transition away from mandatory dollar energy pricing, allowing strategic energy trade to clear in sovereign national currencies."
    },
    {
        "keywords": ["the permission wars", "shanaka anslem perera"],
        "summary": "Shanaka Anslem Perera presents a foundational thesis on monetary sovereignty: the true geopolitical contest is no longer about paper currencies, but about who controls the permissioned infrastructure and switches over global payment rails. The essay details how nations are developing autonomous switches to prevent extraterritorial financial de-platforming.",
        "mechanism": "<b>Infrastructure Switches & Permissioned Rails (Bucket 1.5):</b> Strategic shift from currency competition to the control and defense of the underlying telecommunications, messaging, and ledger rails that grant or deny permission to move money."
    },
    {
        "keywords": ["as the us targets brazil’s payment system", "atlantic council"],
        "summary": "U.S. regulatory scrutiny regarding Brazil's sovereign instant payment network (Pix) and bilateral local-currency trade corridors highlights growing friction over national monetary autonomy. European policymakers are closely observing the dispute as a precedent for regulatory pressures against independent, non-dollar payment rails.",
        "mechanism": "<b>Global Trade Finance & Sovereign Payment Infrastructure (Bucket 1.3):</b> Autonomous sovereign instant payment systems compress transaction friction and provide domestic clearing alternatives independent of Western card and banking monopolies."
    },
    {
        "keywords": ["gold demand set to climb as $29 trillion in sovereign capital", "investinglive"],
        "summary": "Institutional survey data covering $29 trillion in sovereign wealth funds and central bank reserves reveals that 45% of monetary authorities plan to expand gold allocations over the next three years, viewing bullion as the primary hedge against sovereign asset confiscation and persistent U.S. debt expansion.",
        "mechanism": "<b>Central Bank Physical Gold Accumulation (Bucket 2.1):</b> Systemic reallocation of sovereign balance sheets into un-freezable, physically stored gold bullion, surpassing foreign Treasury holdings in multiple key central banks."
    },
    {
        "keywords": ["indonesia and china expand push to reduce us dollar dependence", "visiontimes"],
        "summary": "Bank Indonesia and the People's Bank of China expanded their Local Currency Settlement (LCS) and bilateral currency swap frameworks, reporting record transaction volumes. The bilateral framework enables direct rupiah-yuan settlement for trade, investment, and cross-border QR code retail transactions.",
        "mechanism": "<b>Bilateral Currency Swap Networks & Local Currency Settlement (Bucket 2.6):</b> Central bank swap lines and local currency clearing facilities replace intermediate dollar conversion for comprehensive trade and retail payment flows."
    },
    {
        "keywords": ["bank indonesia credibility under more pressure as oversight tightens", "thebanker"],
        "summary": "A critical review of Indonesian central bank governance and legal oversight reforms, analyzing how central bank autonomy and institutional credibility influence foreign capital inflows, exchange rate stability, and sovereign creditworthiness in developing economies.",
        "mechanism": "<b>Institutional Credibility & Central Bank Governance (Bucket 2.7):</b> Central bank governance trust and political insulation serve as primary determinants of currency stability and foreign reserve allocation choices."
    },
    {
        "keywords": ["rbi unveils draft rules to simplify and expand g-sec trading", "g-sec trading"],
        "summary": "The Reserve Bank of India (RBI) issued comprehensive draft regulations to expand domestic government bond (G-sec) trading and liquidity for non-resident investors, facilitating international portfolio access and paving the way for rupee-denominated sovereign debt globalization.",
        "mechanism": "<b>CIP Arbitrage & Domestic Debt Market Globalization (Bucket 2.5):</b> Expanding non-resident access to domestic sovereign debt markets eases Covered Interest Parity (CIP) frictions and builds non-dollar sovereign debt liquidity pools."
    },
    {
        "keywords": ["bric creator o'neill says a dollar alternative is no longer a 'fantasy'", "biggo.com"],
        "summary": "Jim O'Neill, former Goldman Sachs chief economist who coined the BRIC acronym, stated that creating a viable alternative to the U.S. dollar is no longer unrealistic, driven by the weaponization of the dollar, expanding bilateral trade agreements, and growing institutional collaboration among emerging market central banks.",
        "mechanism": "<b>Alternative Multilateral Currency Architectures (Bucket 2.2):</b> Coordinated policy initiatives by emerging market surplus economies to formalize alternative reserve and settlement frameworks."
    },
    {
        "keywords": ["inflate away the debt? strategic logic and risks of a weak dollar", "geopolitical monitor"],
        "summary": "Geopolitical and macroeconomic analysis details the structural incentives and risks facing the U.S. government regarding sovereign debt sustainability, evaluating the domestic temptation for a weaker currency regime and the resulting loss of international sovereign investor confidence.",
        "mechanism": "<b>Sovereign Debt Denomination & Real Yield Degradation (Bucket 1.2):</b> Declining real returns on USD-denominated sovereign bonds incentivize foreign sovereign debt managers to issue and hold alternative currency paper (Panda bonds, Eurobonds)."
    },
    {
        "keywords": ["bank of china approves a yuan clearing hub across 19 africa", "bitke"],
        "summary": "Bank of China established a comprehensive offshore yuan clearing network spanning 19 African economies, facilitating direct RMB-local currency trade settlements, reducing foreign exchange intermediation losses through the U.S. dollar, and supporting Chinese-African industrial supply chains.",
        "mechanism": "<b>Alternative Clearing Hubs & African Regional Rails (Bucket 2.2):</b> Deployment of direct offshore RMB clearing hubs replaces two-step USD cross-currency conversions with direct local-currency-to-RMB clearing corridors."
    },
    {
        "keywords": ["major financial institutions unveil bank-led on-chain money initiative", "pr newswire"],
        "summary": "A consortium of top global commercial banks launched an on-chain tokenized deposit and interbank settlement network designed for programmable, multi-currency 24/7 cross-border liquidity management, reducing settlement friction without intermediate conversion through U.S. dollars.",
        "mechanism": "<b>Tokenized Sovereign Assets & On-Chain Settlement (Bucket 2.4):</b> Commercial bank tokenized deposits enable multi-currency atomic swaps on distributed ledgers, bypassing traditional correspondent dollar clearing cycles."
    },
    {
        "keywords": ["portability of ai compute infrastructure in ai acquisitions", "mayer brown"],
        "summary": "Legal and infrastructure analysis detailing cross-border AI compute agreements, jurisdictional transfer constraints, and how geopolitical supply-chain regulations impact the valuation of sovereign compute assets and cross-border tech investments.",
        "mechanism": "<b>Convenience Yield & Sovereign Tech Asset Allocation (Bucket 1.4):</b> Technological asset sovereignty and capital control dynamics affecting cross-border investment flows and high-convenience safe asset yields."
    },
    {
        "keywords": ["two key events signal end of dollar's domination", "china daily"],
        "summary": "International economists and state authorities highlight two critical inflection points: the widespread bilateral adoption of local-currency trade settlement across BRICS+ members and historic central bank physical gold acquisitions, marking an accelerating structural transition toward a multipolar currency order.",
        "mechanism": "<b>Bilateral Pricing Agreements & Strategic De-Dollarization (Bucket 2.3):</b> Synchronized macroeconomic policies by surplus nations to replace dollar invoicing with bilateral currency swaps and commodity-backed trade mechanisms."
    }
]

COUNTRY_PATTERNS = {
    "China": [r"\bchina\b", r"\bchinese\b", r"\bbeijing\b", r"\byuan\b", r"\brenminbi\b", r"\bcips\b", r"\bpboc\b"],
    "United States": [r"\bunited states\b", r"\bu\.s\.\b", r"\busa\b", r"\bamerica\b", r"\bwashington\b", r"\bfed\b", r"\bfederal reserve\b", r"\btreasury\b"],
    "Russia": [r"\brussia\b", r"\brussian\b", r"\bmoscow\b", r"\bruble\b", r"\bkremlin\b"],
    "Saudi Arabia": [r"\bsaudi\b", r"\briyadh\b", r"\baramco\b"],
    "Iran": [r"\biran\b", r"\biranian\b", r"\btehran\b"],
    "India": [r"\bindia\b", r"\bindian\b", r"\bdelhi\b", r"\brupee\b", r"\brbi\b"],
    "Brazil": [r"\bbrazil\b", r"\bbrazilian\b", r"\bbrasilia\b", r"\breal\b"],
    "Eurozone/EU": [r"\beuropean union\b", r"\beu\b", r"\beurozone\b", r"\beuro\b", r"\becb\b", r"\bbrussels\b"],
    "Japan": [r"\bjapan\b", r"\bjapanese\b", r"\btokyo\b", r"\byen\b", r"\bboj\b"],
    "UAE": [r"\buae\b", r"\bemirates\b", r"\bdubai\b", r"\babu dhabi\b", r"\bdirham\b"],
    "Indonesia": [r"\bindonesia\b", r"\bindonesian\b", r"\bjakarta\b", r"\brupiah\b"],
    "South Africa": [r"\bsouth africa\b", r"\bsouth african\b", r"\bjohannesburg\b", r"\brand\b"],
    "Libya": [r"\blibya\b", r"\blibyan\b", r"\btripoli\b"],
    "Pakistan": [r"\bpakistan\b", r"\bpakistani\b", r"\bislamabad\b"],
    "Angola": [r"\bangola\b", r"\bangolan\b", r"\bluanda\b"],
    "Hong Kong": [r"\bhong kong\b", r"\bhkma\b", r"\bhkd\b"],
    "UK": [r"\bunited kingdom\b", r"\bbritain\b", r"\bbritish\b", r"\blondon\b", r"\bpound\b", r"\bboe\b"],
    "Mongolia": [r"\bmongolia\b", r"\bmongolian\b", r"\bulaanbaatar\b"]
}

def clean_scraped_text(raw_text):
    """Heuristic cleaner stripping cookie banners, privacy notices, headers, and boilerplate."""
    if not raw_text or str(raw_text).lower() == 'nan':
        return ""
    text = str(raw_text)
    boilerplate = [
        r"we value your privacy.*?(?=(\.|\n|$))",
        r"we and our partners store and/or access information.*?(?=(\.|\n|$))",
        r"cookies and process personal data.*?(?=(\.|\n|$))",
        r"subscribe to read the full article.*?(?=(\.|\n|$))",
        r"all rights reserved.*?(?=(\.|\n|$))",
        r"terms of service.*?(?=(\.|\n|$))",
        r"privacy policy.*?(?=(\.|\n|$))",
        r"more \+ coverage web3 games nfts crypto.*?(?=(\.|\n|$))",
        r"by\s+[a-z\s]+on\s+[a-z0-9,\s]+(?=(\.|\n|$))"
    ]
    for bp in boilerplate:
        text = re.sub(bp, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_countries(text):
    text_lower = str(text).lower()
    found = []
    for country, patterns in COUNTRY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                found.append(country)
                break
    return ", ".join(found) if found else "Global / Multilateral"

def get_best_resolved_url(row):
    b = str(row.get('Resolved_URL_via_BraveSearch', '')).strip()
    g = str(row.get('Resolved_URL_via_GoogleSearch', '')).strip()
    u = str(row.get('URL', '')).strip()
    if b and b.lower() != 'nan' and b.startswith('http'):
        return b
    if g and g.lower() != 'nan' and g.startswith('http'):
        return g
    return u

def get_clean_bucket_name(b_id):
    for b in BUCKET_TAXONOMY:
        if b["id"] == str(b_id).strip(): return b["name"]
    return str(b_id)

def get_clean_bucket_short(b_id):
    clean_map = {
        "1.1": "FX Reserve Composition", "1.2": "International Debt Denomination", "1.3": "Trade Finance & SWIFT/BIS",
        "1.4": "Treasury Yield & Swap Spreads", "1.5": "Trade Policy & Tariffs", "2.1": "Central Bank Physical Gold",
        "2.2": "Alternative Rails (CIPS/mBridge)", "2.3": "Petroyuan & Commodities", "2.4": "Non-USD Stablecoins & Digital Assets",
        "2.5": "CIP Deviations & Treasury Auctions", "2.6": "Bilateral Swaps & Green RMB Bonds", "2.7": "Institutional Credibility & Governance"
    }
    return clean_map.get(str(b_id).strip(), str(b_id))

def get_score_badge_style(score):
    s = max(0.0, min(100.0, float(score)))
    if s >= 70:
        ratio = (s - 70) / 30.0
        g1 = f"rgba(162, 120, 68, {0.85 + 0.15 * ratio:.2f})"
        g2 = f"rgba(140, 42, 28, {0.85 + 0.15 * ratio:.2f})"
        return f"background: linear-gradient(135deg, {g1} 0%, {g2} 100%); color: #FFFFFF; border: none; font-weight: 700; box-shadow: 0 2px 6px rgba(140,42,28,0.25);"
    elif s >= 40:
        ratio = (s - 40) / 30.0
        bg_alpha = 0.15 + 0.20 * ratio
        return f"background: rgba(162, 120, 68, {bg_alpha:.2f}); color: #7A5420; border: 1px solid rgba(162, 120, 68, 0.6); font-weight: 700;"
    elif s >= 15:
        ratio = (s - 15) / 25.0
        bg_alpha = 0.10 + 0.12 * ratio
        return f"background: rgba(195, 185, 172, {bg_alpha:.2f}); color: #574D42; border: 1px solid rgba(195, 185, 172, 0.7); font-weight: 700;"
    else:
        return f"background: rgba(138, 127, 116, 0.08); color: #786D62; border: 0.5px solid rgba(195, 185, 172, 0.6); font-weight: 400;"

def get_curated_summary_and_mechanism(title, bucket_id, raw_text, desc):
    """Retrieves high-quality curated summary & mechanism, or generates cleaned fallback."""
    clean_b_name = get_clean_bucket_name(bucket_id)
    t_lower = str(title).lower()
    
    # 1. Match against LLM curated summary catalog by keyword overlap
    for item in EXECUTIVE_CATALOG:
        for kw in item["keywords"]:
            if kw.lower() in t_lower:
                return item["summary"], item["mechanism"]
    
    # 2. Dynamic Clean Fallback
    cleaned = clean_scraped_text(raw_text)
    if not cleaned or len(cleaned) < 50:
        cleaned = clean_scraped_text(desc)
    
    snippet = cleaned[:280] + "..." if len(cleaned) > 280 else cleaned
    summary_out = snippet if snippet else f"Intelligence report covering key developments in {clean_b_name}."
    mechanism_out = f"<b>Monetary Mechanism ({clean_b_name}):</b> Structural shift in sovereign balance sheet composition, cross-border payment messaging infrastructure, or alternative clearing corridors."
    
    return summary_out, mechanism_out

def build_report():
    print("=================================================================")
    print("📊 Generating Simplified De-Dollarization News Ranking Report (Curated)")
    print("=================================================================")

    # Locate input dataset (prioritize latest updated)
    if os.path.exists("news_dedollarization_sept21_all_ranked.csv"):
        input_csv = "news_dedollarization_sept21_all_ranked.csv"
    elif os.path.exists("news_dedollarization_top30_latest_updated.csv"):
        input_csv = "news_dedollarization_top30_latest_updated.csv"
    elif os.path.exists("news_dedollarization_top30_last20days.csv"):
        input_csv = "news_dedollarization_top30_last20days.csv"
    elif os.path.exists("news_dedollarization_614_eigenmind_equiweighted_ranked.csv"):
        input_csv = "news_dedollarization_614_eigenmind_equiweighted_ranked.csv"
    else:
        candidates = glob.glob("news_*_successful_scrapes.csv") + glob.glob("news_*_fulltext.csv")
        if not candidates:
            print("❌ Error: No news dataset found to generate report from.")
            return False
        input_csv = max(candidates, key=os.path.getmtime)

    print(f"Using dataset: {input_csv}")
    df_all = pd.read_csv(input_csv, dtype={'assigned_bucket_id': str})

    df_all['assigned_bucket_id'] = df_all.get('assigned_bucket_id', '1.1').fillna('1.1').astype(str).str.strip()
    df_all['resolved_url'] = df_all.apply(get_best_resolved_url, axis=1)

    if 'country_tags' not in df_all.columns:
        df_all['full_text_combined'] = (df_all['Title'].fillna('') + ' ' + df_all.get('Description', '').fillna('') + ' ' + df_all.get('Extracted_Article_Text', '').fillna('')).astype(str)
        df_all['country_tags'] = df_all['full_text_combined'].apply(extract_countries)

    if 'composite_eigenmind_score' not in df_all.columns or 'composite_eigenmind_rank' not in df_all.columns:
        print("Computing Equi-Weighted Composite Singularity Scores...")
        df_all['full_text_combined'] = (df_all['Title'].fillna('') + ' ' + df_all.get('Description', '').fillna('') + ' ' + df_all.get('Theme', '').fillna('') + ' ' + df_all.get('Extracted_Article_Text', '').fillna('')).astype(str)
        
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=5000)
        all_texts = df_all['full_text_combined'].tolist() + list(BUCKET_DESCRIPTORS.values())
        matrix = vectorizer.fit_transform(all_texts)
        doc_matrix = matrix[:len(df_all)]
        bucket_matrix = matrix[len(df_all):]

        sims_12 = cosine_similarity(doc_matrix, bucket_matrix)
        sims_12_norm = np.zeros_like(sims_12)
        for k in range(12):
            col = sims_12[:, k]
            max_c = col.max() if col.max() > 0 else 1.0
            sims_12_norm[:, k] = (col / max_c) * 100.0

        df_all['S_concept_equi'] = np.round(np.max(sims_12_norm, axis=1), 2)

        bucket_ids = list(BUCKET_DESCRIPTORS.keys())
        best_bucket_idx = np.argmax(sims_12, axis=1)
        df_all['assigned_bucket_id'] = [bucket_ids[i] for i in best_bucket_idx]

        gen_matrix = TfidfVectorizer(stop_words='english', max_features=2500).fit_transform(df_all['full_text_combined'])
        sim_matrix = cosine_similarity(gen_matrix)
        G = nx.Graph()
        for i in range(len(df_all)): G.add_node(i)
        for i in range(len(df_all)):
            for j in range(i+1, len(df_all)):
                if sim_matrix[i, j] > 0.22: G.add_edge(i, j, weight=sim_matrix[i, j])

        betweenness_dict = nx.betweenness_centrality(G)
        raw_hinge = np.array([betweenness_dict[i] for i in range(len(df_all))])
        H_hinge = (raw_hinge * 100 / max(raw_hinge.max(), 1e-6))

        S_surface = df_all.get('proximity_score', np.ones(len(df_all))*50.0).values
        sorted_by_surface = np.argsort(-S_surface)
        N_lovasz = np.zeros(len(df_all))
        for rank_pos, idx in enumerate(sorted_by_surface):
            if rank_pos == 0: N_lovasz[idx] = 100.0
            else:
                higher_indices = sorted_by_surface[:rank_pos]
                N_lovasz[idx] = max(0.0, (1.0 - np.max(sim_matrix[idx, higher_indices])) * 100.0)

        raw_composite_equi = (0.20 * S_surface) + (0.35 * df_all['S_concept_equi'].values) + (0.25 * N_lovasz) + (0.20 * H_hinge)
        df_all['composite_eigenmind_score'] = np.round(raw_composite_equi * 100 / raw_composite_equi.max(), 2)
        df_all.sort_values(by='composite_eigenmind_score', ascending=False, inplace=True)
        df_all.reset_index(drop=True, inplace=True)
        df_all['composite_eigenmind_rank'] = df_all.index + 1

    # Select Top 20 guaranteeing 12 buckets
    bucket_list = ["1.1", "1.2", "1.3", "1.4", "1.5", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7"]
    selected_indices = set()
    for b_id in bucket_list:
        b_matches = df_all[df_all['assigned_bucket_id'] == b_id]
        if len(b_matches) > 0:
            selected_indices.add(b_matches.index[0])

    for idx in df_all.index:
        if len(selected_indices) >= 20: break
        if idx not in selected_indices: selected_indices.add(idx)

    df_top20 = df_all.loc[list(selected_indices)].copy()
    df_top20.sort_values(by='composite_eigenmind_score', ascending=False, inplace=True)
    df_top20.reset_index(drop=True, inplace=True)

    df_top20['parsed_date'] = pd.to_datetime(df_top20['Date'], errors='coerce')
    df_top20_presented = df_top20.sort_values(by=['parsed_date', 'composite_eigenmind_score'], ascending=[False, False]).copy().reset_index(drop=True)

    top20_urls = set(df_top20['resolved_url'])
    df_remaining = df_all[~df_all['resolved_url'].isin(top20_urls)].copy().reset_index(drop=True)
    df_next50 = df_remaining.head(50).copy()

    df_next50['parsed_date'] = pd.to_datetime(df_next50['Date'], errors='coerce')
    df_next50_presented = df_next50.sort_values(by=['parsed_date', 'composite_eigenmind_score'], ascending=[False, False]).copy().reset_index(drop=True)

    # Build HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Merlin Intelligence — De-Dollarization Macro Intelligence Report: Onto-Semantic Signals, Empirical Indicators & Quantitative Portfolio Synthesis.">
<title>Merlin Intelligence — De-Dollarization Macro Intelligence Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Lora:ital,wght@0,400;0,500;1,400&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">

<style>
:root {{
  --bg:         #F0ECE6;
  --ink:        #14120F;
  --gold:       #A27844;
  --rule:       #C3B9AC;
  --light:      #8A7F74;
  --pale:       #F7F4F0;
  --dark:       #1E1A16;
  --accent:     #8C2A1C;
  --slate:      #3E4B4A;
  --slate-pale: #E7ECEA;
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}
body {{
  background: var(--bg); color: var(--ink);
  font-family: 'Lora', Georgia, serif; font-size: 17px; line-height: 1.72;
  -webkit-font-smoothing: antialiased;
}}
.wrap       {{ max-width: 820px; margin: 0 auto; padding: 0 2rem; }}
.wrap--wide {{ max-width: 1100px; margin: 0 auto; padding: 0 2rem; }}

nav {{ padding: 1.2rem 0 1.0rem; border-bottom: 0.5px solid var(--rule); }}
nav .wrap--wide {{ display: flex; align-items: center; justify-content: space-between; }}
.nav-brand {{
  font-family: 'Space Mono', monospace; font-size: 0.72rem; font-weight: 700;
  letter-spacing: 0.08em; color: var(--ink); text-decoration: none; text-transform: uppercase;
  display: flex; align-items: center; gap: 0.7rem;
}}
.nav-logo {{
  height: 38px; width: 38px; object-fit: cover; display: block;
  border: 0.5px solid var(--rule); border-radius: 50%; padding: 2px; background: var(--pale);
}}
.nav-sub {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; color: var(--light); letter-spacing: 0.04em; }}

.hero {{ padding: 4.5rem 0 3.5rem; position: relative; overflow: hidden; }}
.hero::before {{
  content: ''; position: absolute; inset: 0;
  background-image: repeating-linear-gradient(-62deg, transparent, transparent 80px, rgba(162,120,68,0.055) 80px, rgba(162,120,68,0.055) 80.5px);
  pointer-events: none;
}}
.hero-eyebrow {{ font-family: 'Space Mono', monospace; font-size: 0.68rem; color: var(--gold); letter-spacing: 0.10em; text-transform: uppercase; margin-bottom: 1.2rem; display: block; }}
.hero-headline {{ font-family: 'Playfair Display', serif; font-size: clamp(2.2rem, 5vw, 3.4rem); font-weight: 400; line-height: 1.14; color: var(--ink); margin-bottom: 1.2rem; max-width: 860px; }}
.hero-headline em {{ font-style: italic; color: var(--gold); }}
.hero-sub {{ font-size: 1.05rem; color: var(--light); max-width: 720px; line-height: 1.65; margin-bottom: 2.2rem; }}

.hero-stats {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;
  border-top: 0.5px solid var(--rule); padding-top: 2.0rem; margin-top: 1.5rem;
}}
.stat-item {{ border-left: 2px solid var(--gold); padding-left: 1.0rem; }}
.stat-val {{ font-family: 'Space Mono', monospace; font-size: 1.6rem; font-weight: 700; color: var(--ink); display: block; line-height: 1.2; }}
.stat-lbl {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; color: var(--light); text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.3rem; display: block; }}

@media (max-width: 768px) {{
  .hero-stats {{ grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
}}

main {{ padding: 3.5rem 0; }}
section {{ margin-bottom: 4.5rem; }}
.sec-label {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; color: var(--gold); letter-spacing: 0.10em; text-transform: uppercase; display: block; margin-bottom: 0.6rem; }}
.section-title {{ font-family: 'Playfair Display', serif; font-size: 1.85rem; font-weight: 400; color: var(--ink); margin-bottom: 0.8rem; line-height: 1.25; }}
.section-title em {{ font-style: italic; color: var(--gold); }}
.section-intro {{ font-size: 0.96rem; color: var(--light); max-width: 780px; margin-bottom: 2.0rem; line-height: 1.65; }}

/* Pipeline Architecture Grid */
.pipeline-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.2rem; margin: 2.0rem 0; }}
.pipeline-card {{ border: 0.5px solid var(--rule); background: var(--pale); padding: 1.4rem; display: flex; flex-direction: column; justify-content: space-between; position: relative; }}
.pipeline-step {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; font-weight: 700; color: var(--gold); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; display: block; }}
.pipeline-title {{ font-family: 'Playfair Display', serif; font-size: 1.05rem; font-weight: 600; color: var(--ink); margin-bottom: 0.6rem; line-height: 1.3; }}
.pipeline-desc {{ font-size: 0.82rem; color: var(--light); line-height: 1.5; }}
@media (max-width: 900px) {{ .pipeline-grid {{ grid-template-columns: 1fr 1fr; }} }}
@media (max-width: 600px) {{ .pipeline-grid {{ grid-template-columns: 1fr; }} }}

/* Macro Regime Cards */
.macro-section {{ display: flex; flex-direction: column; gap: 2.2rem; margin: 2.0rem 0; }}
.macro-card {{ border: 0.5px solid var(--rule); background: var(--pale); padding: 2.2rem; }}
.macro-eyebrow {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; color: var(--gold); text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.5rem; }}
.macro-title {{ font-family: 'Playfair Display', serif; font-size: 1.45rem; font-weight: 600; color: var(--ink); margin-bottom: 1.1rem; line-height: 1.3; }}
.macro-title em {{ font-style: italic; color: var(--gold); }}
.macro-body {{ font-size: 0.98rem; color: var(--ink); line-height: 1.74; }}
.macro-body p {{ margin-bottom: 1.1rem; }}
.macro-body p:last-child {{ margin-bottom: 0; }}

.callout-box {{ border-left: 3px solid var(--gold); background: var(--bg); padding: 1.1rem 1.4rem; margin: 1.3rem 0; font-size: 0.92rem; line-height: 1.65; }}
.callout-box strong {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; text-transform: uppercase; color: var(--gold); display: block; margin-bottom: 0.3rem; letter-spacing: 0.05em; }}

.quant-box {{ border-left: 3px solid var(--slate); background: var(--slate-pale); padding: 1.3rem 1.5rem; margin: 1.4rem 0; }}
.quant-box .quant-label {{ font-family: 'Space Mono', monospace; font-size: 0.68rem; font-weight: 700; color: var(--slate); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; }}
.quant-box p {{ margin-bottom: 0.8rem; font-size: 0.94rem; line-height: 1.65; }}
.quant-box p:last-child {{ margin-bottom: 0; }}

/* Corroborating Intelligence / Selected News Box */
.selected-news-box {{
  margin-top: 1.4rem;
  background: var(--bg);
  border: 0.5px solid var(--rule);
  border-left: 3px solid var(--gold);
  padding: 1.1rem 1.4rem;
}}
.selected-news-label {{
  font-family: 'Space Mono', monospace;
  font-size: 0.66rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--gold);
  margin-bottom: 0.75rem;
  display: block;
}}
.selected-news-list {{
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding: 0;
  margin: 0;
}}
.selected-news-item {{
  font-size: 0.88rem;
  line-height: 1.45;
}}
.selected-news-link {{
  font-family: 'Playfair Display', serif;
  font-size: 0.98rem;
  font-weight: 600;
  color: var(--ink);
  text-decoration: none;
  border-bottom: 1px dotted var(--gold);
  transition: color 0.15s ease;
}}
.selected-news-link:hover {{
  color: var(--gold);
}}
.selected-news-meta {{
  font-family: 'Space Mono', monospace;
  font-size: 0.64rem;
  color: var(--light);
  display: block;
  margin-top: 0.2rem;
}}

/* ETF Universe Color Grid */
.etf-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.1rem;
  margin: 1.5rem 0 1.6rem;
}}
@media (max-width: 900px) {{ .etf-grid {{ grid-template-columns: 1fr 1fr; }} }}
@media (max-width: 600px) {{ .etf-grid {{ grid-template-columns: 1fr; }} }}

.etf-card {{
  background: var(--bg);
  border: 0.5px solid var(--rule);
  padding: 1.15rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}
.etf-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}}
.etf-ticker {{
  font-family: 'Space Mono', monospace;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--ink);
  background: rgba(20, 18, 15, 0.08);
  padding: 0.18rem 0.5rem;
  border-radius: 2px;
}}
.etf-alloc {{
  font-family: 'Space Mono', monospace;
  font-size: 0.70rem;
  font-weight: 700;
  color: var(--gold);
}}
.etf-name {{
  font-family: 'Playfair Display', serif;
  font-size: 1.02rem;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 0.45rem;
  line-height: 1.3;
}}
.etf-desc {{
  font-size: 0.82rem;
  line-height: 1.52;
  color: var(--ink);
  margin: 0;
}}

/* Taxonomy Grid */
.taxonomy-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.2rem; margin: 1.8rem 0; }}
.taxonomy-card {{ border: 0.5px solid var(--rule); background: var(--pale); padding: 1.2rem; display: flex; flex-direction: column; justify-content: space-between; }}
.tax-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; }}
.tax-badge {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; font-weight: 700; background: var(--ink); color: var(--bg); padding: 0.15rem 0.5rem; }}
.tax-count {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; color: var(--gold); }}
.tax-title {{ font-family: 'Playfair Display', serif; font-size: 0.98rem; font-weight: 600; color: var(--ink); margin-bottom: 0.4rem; line-height: 1.3; }}
.tax-desc {{ font-size: 0.80rem; color: var(--light); line-height: 1.45; margin: 0; }}

@media (max-width: 900px) {{ .taxonomy-grid {{ grid-template-columns: 1fr 1fr; }} }}
@media (max-width: 600px) {{ .taxonomy-grid {{ grid-template-columns: 1fr; }} }}

/* News Cards */
.news-cards {{ display: flex; flex-direction: column; gap: 1.8rem; margin-top: 1.8rem; }}
.news-card {{ border: 0.5px solid var(--rule); background: var(--pale); padding: 1.8rem; position: relative; transition: transform 0.2s ease, box-shadow 0.2s ease; }}
.news-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(20,18,15,0.04); }}
.card-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 0.8rem; margin-bottom: 0.9rem; flex-wrap: wrap; }}
.card-badges {{ display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }}
.badge-date {{ font-family: 'Space Mono', monospace; font-size: 0.70rem; font-weight: 700; background: var(--ink); color: var(--bg); padding: 0.25rem 0.60rem; }}
.badge-bucket {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; background: rgba(162,120,68,0.12); color: var(--ink); padding: 0.2rem 0.55rem; border: 0.5px solid rgba(162,120,68,0.3); font-weight: 700; }}
.card-title {{ font-family: 'Playfair Display', serif; font-size: 1.30rem; font-weight: 600; line-height: 1.3; color: var(--ink); margin-bottom: 0.7rem; }}
.card-title a {{ color: var(--ink); text-decoration: none; border-bottom: 1px dashed var(--gold); }}
.card-title a:hover {{ color: var(--gold); }}
.card-meta {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; color: var(--light); margin-bottom: 0.8rem; display: block; }}

.country-tags-wrap {{ display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 1.0rem; align-items: center; }}
.country-label {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; color: var(--gold); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; margin-right: 0.2rem; }}
.country-tag {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; color: var(--ink); background: var(--bg); border: 0.5px solid var(--rule); padding: 0.12rem 0.45rem; border-radius: 2px; }}

.card-summary {{ font-size: 0.94rem; color: var(--ink); line-height: 1.65; margin-bottom: 1.1rem; }}
.card-mechanism {{ border-left: 2.5px solid var(--gold); padding: 0.75rem 1rem; background: var(--bg); font-size: 0.88rem; color: var(--ink); line-height: 1.6; }}
.card-mechanism strong {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; text-transform: uppercase; color: var(--gold); display: block; margin-bottom: 0.25rem; letter-spacing: 0.05em; }}

/* Table */
.table-wrap {{ overflow-x: auto; margin-top: 1.8rem; border: 0.5px solid var(--rule); }}
table {{ width: 100%; border-collapse: collapse; background: var(--pale); font-size: 0.88rem; text-align: left; }}
th {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--gold); padding: 0.9rem 0.85rem; border-bottom: 1px solid var(--rule); background: var(--bg); }}
td {{ padding: 0.85rem; border-bottom: 0.5px solid var(--rule); vertical-align: middle; }}
tr:last-child td {{ border-bottom: none; }}
tr:hover {{ background: rgba(162,120,68,0.04); }}
.td-date {{ font-family: 'Space Mono', monospace; font-weight: 700; color: var(--ink); width: 110px; }}
.td-bucket {{ font-family: 'Space Mono', monospace; font-size: 0.65rem; color: var(--light); width: 160px; }}
.td-countries {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; color: var(--ink); width: 180px; }}
.td-title {{ font-family: 'Playfair Display', serif; font-size: 0.96rem; color: var(--ink); }}
.td-title a {{ color: var(--ink); text-decoration: none; }}
.td-title a:hover {{ color: var(--gold); text-decoration: underline; }}

footer {{ padding: 2.5rem 0; border-top: 0.5px solid var(--rule); margin-top: 3.5rem; font-family: 'Space Mono', monospace; font-size: 0.65rem; color: var(--light); }}
footer .wrap--wide {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; }}
</style>
</head>
<body>

<nav>
  <div class="wrap--wide">
    <a href="#" class="nav-brand">
      <img src="MI-icon.png" alt="Merlin Intelligence" class="nav-logo" onerror="this.style.display='none'">
      <span>Merlin Intelligence — De-Dollarization Intelligence</span>
    </a>
    <span class="nav-sub">Geoeconomic Signal Intelligence & Macro Synthesis • September 2026</span>
  </div>
</nav>

<header class="hero">
  <div class="wrap--wide">
    <span class="hero-eyebrow">Geoeconomic Signal Intelligence & Macro Synthesis</span>
    <h1 class="hero-headline">De-Dollarization Signals: <em>Macro Intelligence & Empirical Indicators</em></h1>
    <p class="hero-sub">
      Comprehensive intelligence evaluation of {len(df_all)} clean full-text news articles across 12 empirical indicator categories, synthesizing onto-semantic signals with quantitative macro portfolio dynamics.
    </p>

    <div class="hero-stats">
      <div class="stat-item"><span class="stat-val">{len(df_all)}</span><span class="stat-lbl">Clean Full-Text Articles</span></div>
      <div class="stat-item"><span class="stat-val">12</span><span class="stat-lbl">Indicator Buckets Covered</span></div>
      <div class="stat-item"><span class="stat-val">20</span><span class="stat-lbl">Priority Focus Intelligence</span></div>
      <div class="stat-item"><span class="stat-val">50</span><span class="stat-lbl">Extended Coverage Articles</span></div>
    </div>
  </div>
</header>

<main class="wrap--wide">

  <!-- SECTION 01: PIPELINE ARCHITECTURE -->
  <section id="pipeline">
    <span class="sec-label">01. Intelligence Pipeline Architecture</span>
    <h2 class="section-title">From Onto-Graph to Seeds, Signals, and News Bucketing</h2>
    <p class="section-intro">
      The Merlin Intelligence news analysis engine operates on an end-to-end onto-semantic architecture. Rather than relying on simple keyword scraping or ungrounded summaries, the pipeline enforces formal semantic constraints from knowledge representation down to individual news classification:
    </p>

    <div class="pipeline-grid">
      <div class="pipeline-card">
        <div>
          <span class="pipeline-step">Phase 01 // Ontology</span>
          <h3 class="pipeline-title">The Onto-Semantic Graph</h3>
          <p class="pipeline-desc">
            Constructing a formal directed knowledge graph mapping global monetary actors (central banks, sovereign wealth funds), institutional standards (IMF COFER, SWIFT messaging, BIS OTC turnover), market mechanisms (CIP deviations, Treasury convenience yields, swap spreads), and alternative transaction rails (CIPS, mBridge, multi-CBDC corridors, stablecoins).
          </p>
        </div>
      </div>

      <div class="pipeline-card">
        <div>
          <span class="pipeline-step">Phase 02 // Taxonomy</span>
          <h3 class="pipeline-title">Algorithmic Seed Generation</h3>
          <p class="pipeline-desc">
            Projecting topological graph centrality hubs and cross-boundary bridge nodes into a curated taxonomy of 100 domain-specific search query seeds across 12 empirical indicator buckets. Seeds target specific monetary mechanics (e.g., Panda bond debuts, non-SWIFT messaging, Treasury auction tailing) rather than generic media noise.
          </p>
        </div>
      </div>

      <div class="pipeline-card">
        <div>
          <span class="pipeline-step">Phase 03 // Harvesting</span>
          <h3 class="pipeline-title">Harvesting & Canonical Resolution</h3>
          <p class="pipeline-desc">
            Querying Google News RSS feeds across multi-week lookback windows, resolving raw URLs to canonical publisher links via Brave Search APIs to eliminate aggregator redirects, and deploying concurrent headless Chromium Playwright workers to extract clean, un-gated full-text journalistic content.
          </p>
        </div>
      </div>

      <div class="pipeline-card">
        <div>
          <span class="pipeline-step">Phase 04 // Immersion</span>
          <h3 class="pipeline-title">Multi-Anchor Concept Bucketing</h3>
          <p class="pipeline-desc">
            Vectorizing clean full texts and computing high-dimensional similarity against the multi-anchor semantic descriptors of the 12 empirical indicator buckets. Each article is assigned to its dominant category based on concept immersion, guaranteeing continuous calibration across all dimensions of monetary realignment.
          </p>
        </div>
      </div>
    </div>
  </section>

  <!-- SECTION 02: MACRO OBSERVATIONS -->
  <section id="macro-observations">
    <span class="sec-label">02. Macro Regime Observations</span>
    <h2 class="section-title">Empirical Signals & Model Observations</h2>
    <p class="section-intro">
      Synthesizing real-world news signals harvested across September 2026 with the empirical findings of our 9-Asset Walk-Forward Portfolio K-Max strategy reveals profound structural shifts across energy, sovereign debt, foreign exchange reserves, and global macro portfolio allocations:
    </p>

    <div class="macro-section">

      <!-- SUBSECTION 1: ENERGY & DOLLAR -->
      <article class="macro-card">
        <span class="macro-eyebrow">Macro Observation · 01</span>
        <h3 class="macro-title">Interactions Between Energy Prices and Dollar Dynamics</h3>
        <div class="macro-body">
          <p>
            The escalation of geopolitical friction in the Persian Gulf and maritime interdictions around the Strait of Hormuz have injected sharp risk premia into global crude oil and liquefied natural gas (LNG) markets. Historically, energy supply shocks triggered an automatic, mechanical surge in structural demand for U.S. dollars through the mandatory petrodollar invoicing framework established in 1974, followed by the predictable recycling of petrodollars into U.S. Treasuries.
          </p>
          <p>
            Today, that structural transmission mechanism is breaking down. Major oil exporters and importers—spanning Saudi Arabia, the UAE, Iran, Russia, China, and India—are aggressively deploying non-dollar settlement corridors. Hydrocarbon transactions are increasingly cleared directly in renminbi (the petroyuan), UAE dirhams, and local currencies, bypassing traditional New York correspondent clearing banks and SWIFT rails.
          </p>
          <p>
            Consequently, rising energy prices no longer drive structural foreign accumulation of U.S. Treasuries. Instead, energy inflation functions as an un-hedged terms-of-trade shock against Western economies, expanding trade deficits and driving domestic import inflation, while Eurasian energy trade loops become self-contained, insulated from U.S. dollar liquidity constraints.
          </p>

          <div class="selected-news-box">
            <span class="selected-news-label">Corroborating Intelligence · Selected News</span>
            <ul class="selected-news-list">
              <li class="selected-news-item">
                <a href="https://energy.economictimes.indiatimes.com/news/oil-and-gas/oil-trades-shift-towards-a-currency-agnostic-future/133903259" target="_blank" rel="noopener" class="selected-news-link">Oil trade’s shift towards a currency-agnostic future</a>
                <span class="selected-news-meta">ET EnergyWorld • September 08, 2026 • Petroyuan expansion, bilateral crude clearing & bypass of SWIFT rails</span>
              </li>
              <li class="selected-news-item">
                <a href="https://fortune.com/2026/09/11/oil-prices-hormuz-diplomacy-saudi-arabia-houthis-pakistan-us-bab-al-mandab/" target="_blank" rel="noopener" class="selected-news-link">Oil prices dive on signs of Hormuz diplomacy while Saudi Arabia is left hanging in fight vs. Houthis</a>
                <span class="selected-news-meta">Fortune • September 11, 2026 • Persian Gulf maritime bottlenecks, Bab al-Mandab security & geopolitical crude risk premia</span>
              </li>
              <li class="selected-news-item">
                <a href="https://www.europesays.com/3233377/" target="_blank" rel="noopener" class="selected-news-link">US-Iran Conflict Reignites as Hedge Funds Push Crude Oil Bullish Bets to Highest Since May</a>
                <span class="selected-news-meta">BigGo Finance / EuropeSays • September 04, 2026 • Geopolitical crude supply shocks & speculative energy positioning</span>
              </li>
            </ul>
          </div>
        </div>
      </article>

      <!-- SUBSECTION 2: GLOBAL BONDS SELL-OFF -->
      <article class="macro-card">
        <span class="macro-eyebrow">Macro Observation · 02</span>
        <h3 class="macro-title">Global Bonds Sell-Off and Spiking Interest Rates</h3>
        <div class="macro-body">
          <p>
            Sovereign debt markets across G7 economies are experiencing severe duration repricing and yield curve steepening. The U.S. 10-year Treasury yield surged toward 4.86% (3-year highs), while the 30-year bond breached 5.30%—its highest level in 19 years. Concurrently, European government bond yields have pushed higher, undermining traditional fixed-income capital preservation assumptions.
          </p>
          <p>
            In a pivotal warning published in early September 2026, European Central Bank (ECB) economists highlighted an unprecedented crowding-out dynamic: a massive bonanza of bond sales by U.S. mega-cap technology giants is absorbing global institutional fixed-income demand, pulling capital directly away from European sovereign debt and driving up public borrowing costs across the Eurozone. When high-yielding U.S. corporate balance sheets compete for long-term duration capital, sovereign issuers lose their historic yield insulation.
          </p>
          <p>
            This duration sell-off was compounded on September 9, 2026, when the U.S. Treasury under Secretary Scott Bessent conducted its first debt buyback operation. Offering a modest $6 billion against Wall Street expectations of $8–10 billion, the cosmetic intervention backfired, triggering an aggressive yield spike as primary dealers realized that official debt repurchase capacity cannot keep pace with multi-trillion-dollar federal deficits. The structural compression of the Treasury "convenience yield" and persistent deeply negative interest rate swap spreads confirm that sovereign debt is no longer treated as pristine, unassailable safe-haven ballast.
          </p>

          <div class="selected-news-box">
            <span class="selected-news-label">Corroborating Intelligence · Selected News</span>
            <ul class="selected-news-list">
              <li class="selected-news-item">
                <a href="https://www.euractiv.com/news/us-tech-bond-bonanza-could-raise-european-borrowing-costs-say-ecb-analysts/" target="_blank" rel="noopener" class="selected-news-link">US tech bond bonanza could raise European borrowing costs, say ECB analysts</a>
                <span class="selected-news-meta">Euractiv • September 01, 2026 • Mega-cap US corporate debt crowding out European sovereign debt demand</span>
              </li>
              <li class="selected-news-item">
                <a href="https://www.tradingview.com/news/stocktwits:951f65fe9094b:0-the-weekly-spread-what-shaped-yields-and-the-dollar-this-week/" target="_blank" rel="noopener" class="selected-news-link">The Weekly Spread: What Shaped Yields And The Dollar This Week</a>
                <span class="selected-news-meta">TradingView • September 19, 2026 • G7 duration steepening, swap spread compression & Treasury convenience yield erosion</span>
              </li>
            </ul>
          </div>
        </div>
      </article>

      <!-- SUBSECTION 3: 20-YEAR AUCTION HISTORIC DEGRADATION -->
      <article class="macro-card">
        <span class="macro-eyebrow">Macro Observation · 03</span>
        <h3 class="macro-title">Historic Demand Degradation in the U.S. Treasury's September 20-Year Auction</h3>
        <div class="macro-body">
          <div class="callout-box">
            <strong>Key Empirical Observation</strong>
            The U.S. Treasury's September 20-year bond auction experienced historic demand degradation, with primary dealers forced to absorb an unusually large share as foreign indirect bidder participation declined sharply, causing a substantial auction tail.
          </div>
          <p>
            On Wednesday, September 16, 2026, the U.S. Treasury conducted its scheduled 20-year sovereign bond auction, which resulted in the worst demand showing in the security’s history. Foreign indirect bidders—the primary proxy for foreign central banks, sovereign wealth funds, and international institutional reserve managers—withdrew significantly from the bidding book.
          </p>
          <p>
            Faced with an acute absence of foreign sponsor appetite, primary dealers were forced to warehouse an abnormally large percentage of the issued paper. The auction cleared with a dramatic tail above the pre-auction when-issued yield, signaling severe dealer balance sheet indigestion. This auction failure represents concrete empirical evidence that international sovereign allocators are unwilling to finance expanding U.S. fiscal deficits at the long end of the curve without substantial concession premiums, validating our model's structural penalization of long-duration paper.
          </p>

          <div class="selected-news-box">
            <span class="selected-news-label">Corroborating Intelligence · Selected News</span>
            <ul class="selected-news-list">
              <li class="selected-news-item">
                <a href="https://protos.com/us-20-year-bond-auction-just-had-its-worst-showing-ever/" target="_blank" rel="noopener" class="selected-news-link">US 20-year bond auction just had its worst showing ever</a>
                <span class="selected-news-meta">Protos / Cryptonews.net • September 16, 2026 • Historic auction tail, primary dealer balance-sheet indigestion & foreign buyer retreat</span>
              </li>
              <li class="selected-news-item">
                <a href="https://wolfstreet.com/2026/09/15/some-thoughts-on-the-5-42-yield-at-the-20-year-treasury-auction-bond-market-bloodbath-continues/" target="_blank" rel="noopener" class="selected-news-link">U.S. Treasury's $13 Billion 20-Year Bond Auction Yields Record 5.42%; 10-Year Tops 5% for First Time Since 2007</a>
                <span class="selected-news-meta">Wolf Street / BigGo Finance • September 16, 2026 • Long-duration sovereign bond supply overload & foreign central bank buyer strike</span>
              </li>
            </ul>
          </div>
        </div>
      </article>

      <!-- SUBSECTION 4: DE-RESERVIFICATION, NOT DE-DOLLARIZATION -->
      <article class="macro-card">
        <span class="macro-eyebrow">Macro Observation · 04</span>
        <h3 class="macro-title">De-Reservification, Not De-Dollarization</h3>
        <div class="macro-body">
          <p>
            A persistent conceptual error in financial discourse is conflating the U.S. dollar's role as a transactional clearing currency with its role as a permanent sovereign reserve anchor. As articulated by Brad Setser (Council on Foreign Relations) and corroborated by recent Federal Reserve Bank of New York research, the global economy is not abruptly abandoning the dollar for daily trade settlement. In foreign exchange turnover, trade invoicing, and SWIFT messaging, the dollar remains the undisputed operational medium of exchange.
          </p>
          <p>
            What is underway is a calculated, structural process of <strong>De-reservification</strong>: sovereign central banks and monetary authorities are systematically curtailing their long-term foreign exchange exposure to freezeable, debt-monetized G7 sovereign paper. Following the precedent of Western central bank asset freezes in 2022, sovereign reserve managers recognize that holding excess wealth in U.S. Treasuries carries existential counterparty and geopolitical risk.
          </p>
          <p>
            Consequently, sovereign balance sheets are executing an aggressive asset substitution into un-freezable, un-encumbered physical assets—foremost among them, physical gold bullion:
          </p>
          <ul style="margin: 0.8rem 0 1.2rem 1.6rem; font-size: 0.95rem; line-height: 1.65;">
            <li><strong>Sovereign Vault Repatriation:</strong> The Dutch Central Bank (DNB) formally transferred sovereign gold to domestic military vaults, affirming that when multilateral paper guarantees fail, physical bullion is the ultimate monetary anchor.</li>
            <li><strong>Uninterrupted Official Accumulation:</strong> The People's Bank of China (PBoC) expanded its physical gold holdings for 22 consecutive months, lifting official bullion reserves to 2,366 metric tons (76.73 million ounces).</li>
            <li><strong>Institutional Reallocation Intent:</strong> Global central bank surveys indicate that 45% of monetary authorities plan to expand gold reserves over the next 12 to 36 months, allowing maturing Treasury tranches to expire without reinvestment.</li>
          </ul>

          <div class="selected-news-box">
            <span class="selected-news-label">Corroborating Intelligence · Selected News</span>
            <ul class="selected-news-list">
              <li class="selected-news-item">
                <a href="https://www.europesays.com/3239271/" target="_blank" rel="noopener" class="selected-news-link">Dollar's declining reserve share reflects few countries' choices, not global shift, NY Fed says</a>
                <span class="selected-news-meta">Federal Reserve Bank of NY / EuropeSays • September 08, 2026 • Transactional clearing medium vs. sovereign reserve asset allocation dichotomy</span>
              </li>
              <li class="selected-news-item">
                <a href="https://goldsilver.com/industry-news/goldsilver-news/pboc-gold-reserves-august-2026-22-months/" target="_blank" rel="noopener" class="selected-news-link">China Just Broke Its Own Gold-Buying Record. Then Broke It Again.</a>
                <span class="selected-news-meta">GoldSilver • September 07, 2026 • PBoC official gold reserves reach 2,366 tons across 22 consecutive months of official bullion accumulation</span>
              </li>
              <li class="selected-news-item">
                <a href="https://www.cointribune.com/en/china-holds-2366-tons-of-gold-as-yuan-ambitions-grow" target="_blank" rel="noopener" class="selected-news-link">China Holds 2,366 Tons Of Gold As Yuan Ambitions Grow</a>
                <span class="selected-news-meta">Cointribune • September 17, 2026 • Physical bullion reserves as an un-freezable sovereign balance sheet shield against dollar dominance</span>
              </li>
              <li class="selected-news-item">
                <a href="https://www.inventiva.co.in/trends/where-the-worlds-gold-is-going-and-what-china-india-europe-and-america-know-about-the-next-financial-shock/" target="_blank" rel="noopener" class="selected-news-link">Where The World's Gold Is Going And What Central Banks Know About The Next Financial Shock</a>
                <span class="selected-news-meta">Inventiva • September 17, 2026 • Sovereign vault repatriation, Western asset freezes & de-reservification trends across Eurasia</span>
              </li>
            </ul>
          </div>
        </div>
      </article>

      <!-- SUBSECTION 5: QUANT MACRO DYNAMICS (K-MAX) -->
      <article class="macro-card">
        <span class="macro-eyebrow">Macro Observation · 05</span>
        <h3 class="macro-title">Quant Macro Dynamics: Capital Allocation to Dollar by Global Macro Players Remains Strong</h3>
        <div class="macro-body">
          <p>
            The mathematical findings of our institutional research report, <em>Global Macro Expansion: Institutional Quantitative Evaluation of the 9-Asset Walk-Forward Portfolio K-Max Strategy (2018–2026)</em> (evaluating 2,063 live trading sessions across <code>SPY, GLD, UUP, TLT, IEF, LSHUX, DBC, EEM, MCHI</code>), provide rigorous mathematical validation for this dual-currency reality.
          </p>
          <p>
            In the live target allocation heading into the current cycle (market close Friday, September 18, 2026), the proprietary Merlin Asset Allocation model maintains a commanding capital allocation in the U.S. dollar cash proxy (<code>UUP</code>) at <strong>+37.24% of total portfolio capital</strong> (historically averaging a <strong>33.66%</strong> mean capital weight over the trailing 3-year cycle).
          </p>

          <div class="quant-box">
            <div class="quant-label">Systemic Capital Allocation & Balance Sheet Deployment</div>
            <p>
              At this macro intelligence stage, our analysis focuses primarily on <strong>strategic capital allocation</strong> across the portfolio's core asset classes. While detailed mathematical risk allocations (including Euler percentage risk contributions, covariance decompositions, and sensitivity profiles) are generated continuously by our engine and remain available for finer institutional analysis, capital allocation provides the most direct reflection of real-world balance sheet deployment:
            </p>

            <div class="callout-box" style="margin: 1.1rem 0; border-left: 3px solid var(--gold); background: var(--bg);">
              <strong style="font-family: 'Space Mono', monospace; font-size: 0.68rem; text-transform: uppercase; color: var(--gold); letter-spacing: 0.06em; margin-bottom: 0.4rem; display: block;">
                Quant-Attractivity of the Dollar: Primary Capital Anchor
              </strong>
              <p style="font-size: 0.94rem; line-height: 1.65; margin: 0; color: var(--ink);">
                <strong>US Dollar Reserve as Primary Capital Anchor (<code>UUP</code>: +37.24% Capital, +3.14% %RC):</strong><br>
                The US Dollar holding sits at <strong>37.24%</strong> of total capital. With global central banks navigating currency fragmentation and US cash yields remaining attractive, <code>UUP</code> provides stable carry without duration risk, dampening total portfolio volatility to an ultra-low <strong>3.45%</strong> annualized.
              </p>
            </div>

            <p>
              <strong>Cash & Sovereign Safe-Haven Core:</strong> The U.S. dollar cash proxy (<code>UUP</code>: <strong>37.24%</strong>), Intermediate Treasuries (<code>IEF</code>: <strong>16.56%</strong>), and Long Treasuries (<code>TLT</code>: <strong>13.65%</strong>) together command <strong>67.45% of the fund's total capital</strong>. This massive balance-sheet anchor insulates the fund against broad market liquidity freezes, successfully dampening annualized portfolio volatility to an institutional <strong>3.45%</strong>.
            </p>
            <p>
              <strong>Real Assets & Compounding Growth:</strong> Growth capital is concentrated in <strong>Physical Gold (<code>GLD</code>: delivering 65.79% of total portfolio risk-adjusted compounding efficiency</strong>, +125.79% 3Y return), <strong>Broad Commodities (<code>DBC</code>: +18.50% capital</strong>, +18.90% 3Y return) to hedge Middle Eastern energy supply shocks and maritime choke points, and <strong>Large-Cap Equities (<code>SPY</code>: +19.71% capital</strong>, +54.67% 3Y return).
            </p>
            <p>
              <strong>Tactical Factor Hedges:</strong> Disciplined short/hedged sleeves in active growth (<code>LSHUX</code>: <strong>-2.53%</strong>) and Chinese equities (<code>MCHI</code>: <strong>-2.44%</strong>) neutralize valuation crowding and regional balance-sheet restructuring.
            </p>
            <p style="font-size: 0.84rem; color: var(--light); font-style: italic; margin-top: 0.6rem;">
              * Institutional Note: Granular Euler risk decompositions (%RC), asset beta profiles, and stress-test sensitivity matrices are available upon request for finer institutional risk due diligence.
            </p>
          </div>

          <h4 style="font-family: 'Playfair Display', serif; font-size: 1.18rem; margin: 1.8rem 0 0.8rem; color: var(--ink);">
            The 9-Asset Investment Universe: Strategic Profiles & Macro Roles
          </h4>
          <p style="font-size: 0.92rem; color: var(--light); margin-bottom: 1.2rem;">
            Each asset within the K-Max investment universe fulfills a distinct structural mandate across compounding, safe-haven liquidity, duration buffering, and factor hedging:
          </p>

          <div class="etf-grid">
            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">SPY</span>
                <span class="etf-alloc">+19.71% Capital</span>
              </div>
              <h5 class="etf-name">SPDR S&P 500 ETF Trust</h5>
              <p class="etf-desc">
                Core large-cap equity beta proxy (+54.67% 3Y return). Captures high-margin technological productivity and AI capex monetization of premier U.S. corporate balance sheets, disciplined by the model to harvest equity risk premia.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">GLD</span>
                <span class="etf-alloc">Primary Compounding Driver</span>
              </div>
              <h5 class="etf-name">SPDR Gold Shares</h5>
              <p class="etf-desc">
                Physical gold bullion vaulted in London (+125.79% 3Y return). The strategy's primary compounding pillar, delivering 65.79% of total portfolio risk-adjusted compounding efficiency as central bank de-reservification accelerates.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">UUP</span>
                <span class="etf-alloc">+37.24% Capital (+3.14% %RC)</span>
              </div>
              <h5 class="etf-name">Invesco DB US Dollar Index</h5>
              <p class="etf-desc">
                Primary Capital Anchor (37.24% capital). With global central banks navigating currency fragmentation and US cash yields remaining attractive, UUP provides stable carry without duration risk, dampening total portfolio volatility to an ultra-low 3.45% annualized.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">TLT</span>
                <span class="etf-alloc">+13.65% Capital</span>
              </div>
              <h5 class="etf-name">iShares 20+ Year Treasury</h5>
              <p class="etf-desc">
                Ultra-long sovereign duration (~16.5-year duration; -14.36% 3Y return). Constrained and disciplined by the model due to expanding federal deficits, term-premium resurgence, and severe auction demand degradation.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">IEF</span>
                <span class="etf-alloc">+16.56% Capital</span>
              </div>
              <h5 class="etf-name">iShares 7-10 Year Treasury</h5>
              <p class="etf-desc">
                Intermediate-term sovereign duration (~7.2-year duration; +4.12% 3Y return). Delivers positive carry yield and dependable safe-haven liquidity buffer without the acute convexity drawdowns inherent to the ultra-long curve.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">LSHUX</span>
                <span class="etf-alloc">-2.53% Net Capital</span>
              </div>
              <h5 class="etf-name">Loomis Sayles Growth Sleeve</h5>
              <p class="etf-desc">
                Active large-cap growth factor sleeve, tactically shorted / hedged. Deployed by the model to isolate pure market beta, strip out excessive valuation multiples, and shield capital from tech-crowding momentum unwinds.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">DBC</span>
                <span class="etf-alloc">+18.50% Capital</span>
              </div>
              <h5 class="etf-name">Invesco DB Commodity Index</h5>
              <p class="etf-desc">
                Diversified basket of 14 physical commodities across crude, metals, and agriculture (+18.90% 3Y return). Serves as the primary active inflation buffer to hedge Persian Gulf maritime blockades and terms-of-trade shocks.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">EEM</span>
                <span class="etf-alloc">Decoupling Proxy</span>
              </div>
              <h5 class="etf-name">iShares MSCI Emerging Markets</h5>
              <p class="etf-desc">
                Broad emerging market equity exposure outside the G7 (+87.10% 3Y return). Captures sovereign trade reorganization, critical mineral exporters, and semiconductor manufacturing nodes across non-aligned trading corridors.
              </p>
            </div>

            <div class="etf-card">
              <div class="etf-header">
                <span class="etf-ticker">MCHI</span>
                <span class="etf-alloc">-2.44% Net Capital</span>
              </div>
              <h5 class="etf-name">iShares MSCI China ETF</h5>
              <p class="etf-desc">
                Comprehensive Chinese equity exposure, tactically hedged (-16.82% 3Y return). Balances bilateral trade frictions, property sector deleveraging, and deflation against asymmetric upside from state-directed liquidity.
              </p>
            </div>
          </div>

          <p>
            <strong>Institutional Takeaway:</strong> Global systematic macro players allocate heavily to the U.S. dollar not as a long-term speculative store of value, but as an indispensable <em>operational clearing liquidity and zero-beta collateral anchor</em>. Wealth preservation and compounding return generation have decisively decoupled into un-encumbered physical gold and geopolitical commodities, while the dollar provides the liquidity chassis upon which modern quantitative asset allocation operates.
          </p>
        </div>
      </article>

    </div>
  </section>

  <!-- SECTION 03: TAXONOMY OVERVIEW -->
  <section id="categories">
    <span class="sec-label">03. Indicator Categories Overview</span>
    <h2 class="section-title">The 12 Empirical Indicator Categories</h2>
    <p class="section-intro">
      Each harvested piece of news is evaluated across the 12 empirical dimensions of systemic monetary realignment:
    </p>

    <div class="taxonomy-grid">
"""

    for b in BUCKET_TAXONOMY:
        b_id = b["id"]
        b_name = html.escape(b["name"])
        b_desc = html.escape(b["desc"])
        b_count = len(df_all[df_all['assigned_bucket_id'] == b_id])
        html_content += f"""
      <div class="taxonomy-card">
        <div>
          <div class="tax-header">
            <span class="tax-badge">BUCKET {b_id}</span>
            <span class="tax-count">{b_count} Articles</span>
          </div>
          <h3 class="tax-title">{b_name}</h3>
          <p class="tax-desc">{b_desc}</p>
        </div>
      </div>
"""

    html_content += """
    </div>
  </section>

  <!-- SECTION 04: PRIORITY INTELLIGENCE (TOP 20) -->
  <section id="top20">
    <span class="sec-label">04. Priority Intelligence (Top 20 Curated News)</span>
    <h2 class="section-title">Top 20 Priority News Articles: <em>Chronological Presentation & Structural Mechanisms</em></h2>
    <p class="section-intro">
      The 20 articles below guarantee complete representation across all 12 indicator categories. They link directly to their canonical publisher source URLs, presented chronologically starting with the <b>most recent publication date</b> down to earlier news:
    </p>

    <div class="news-cards">
"""

    for idx, row in df_top20_presented.iterrows():
        pres_num = idx + 1
        b_id = str(row['assigned_bucket_id'])
        clean_b_name = html.escape(get_clean_bucket_name(b_id))
        
        title = html.escape(str(row['Title']))
        resolved_target = html.escape(str(row.get('resolved_url', row.get('URL', ''))))
        date_val = html.escape(str(row['Date']))
        
        countries_str = str(row.get('country_tags', 'Global / Multilateral'))
        country_list = [c.strip() for c in countries_str.split(',')]
        country_badges_html = "".join([f'<span class="country-tag">{html.escape(c)}</span>' for c in country_list])
        
        raw_text = str(row.get('Extracted_Article_Text', ''))
        raw_desc = str(row.get('Description', ''))
        curated_summary, curated_mechanism = get_curated_summary_and_mechanism(row['Title'], b_id, raw_text, raw_desc)
        
        html_content += f"""
      <article class="news-card">
        <div class="card-header">
          <div class="card-badges">
            <span class="badge-date">DATE: {date_val}</span>
            <span class="badge-bucket">BUCKET {b_id}: {clean_b_name}</span>
          </div>
          <span class="nav-sub">Priority Focus • {pres_num:02d} of 20</span>
        </div>

        <h3 class="card-title"><a href="{resolved_target}" target="_blank" rel="noopener">{title}</a></h3>
        <span class="card-meta">Publication Date: {date_val} • Direct Source: <a href="{resolved_target}" target="_blank" rel="noopener" style="color:var(--gold); text-decoration:none;">{resolved_target[:75]}...</a></span>

        <div class="country-tags-wrap">
          <span class="country-label">📍 Countries Mentioned:</span>
          {country_badges_html}
        </div>

        <p class="card-summary"><b>Executive Summary:</b> {curated_summary}</p>

        <div class="card-mechanism">
          <strong>Underlying Monetary Mechanism</strong>
          {curated_mechanism}
        </div>
      </article>
"""

    html_content += """
    </div>
  </section>

  <!-- SECTION 05: EXTENDED COVERAGE (FOLLOWING 50) -->
  <section id="next50">
    <span class="sec-label">05. Extended Coverage (Following 50 Articles)</span>
    <h2 class="section-title">Following 50 News Articles: <em>Chronological Reference</em></h2>
    <p class="section-intro">
      The table below displays extended coverage across the following 50 articles from the curated corpus, linking directly to canonical publisher source URLs, ordered by publication date (most recent first):
    </p>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Indicator Category</th>
            <th>Countries Mentioned</th>
            <th>Article Title & Resolved Source Link</th>
          </tr>
        </thead>
        <tbody>
"""

    for idx, row in df_next50_presented.iterrows():
        date_val = html.escape(str(row['Date']))
        b_id = str(row['assigned_bucket_id'])
        clean_b_short = html.escape(get_clean_bucket_short(b_id))
        
        countries_str = str(row.get('country_tags', 'Global / Multilateral'))
        country_list = [c.strip() for c in countries_str.split(',')]
        country_inline = ", ".join(country_list[:3])
        if len(country_list) > 3: country_inline += f" (+{len(country_list)-3})"
        country_inline_html = html.escape(country_inline)
        
        title = html.escape(str(row['Title']))
        resolved_target = html.escape(str(row.get('resolved_url', row.get('URL', ''))))
        
        html_content += f"""
          <tr>
            <td class="td-date">{date_val}</td>
            <td class="td-bucket">[{b_id}] {clean_b_short}</td>
            <td class="td-countries">{country_inline_html}</td>
            <td class="td-title"><a href="{resolved_target}" target="_blank" rel="noopener">{title}</a></td>
          </tr>
"""

    html_content += """
        </tbody>
      </table>
    </div>
  </section>

</main>

<footer>
  <div class="wrap--wide">
    <span>&copy; 2026 Merlin Intelligence. Geoeconomic Knowledge Infrastructure.</span>
    <span>Generated by Merlin Intelligence Pipeline</span>
  </div>
</footer>

</body>
</html>
"""

    f1 = "dedollarization_intelligence_report.html"
    f2 = "dedollarization_intelligence_report_v2.html"

    with open(f1, "w", encoding="utf-8") as f: f.write(html_content)
    with open(f2, "w", encoding="utf-8") as f: f.write(html_content)

    art_dir = r"C:\Users\franc\.gemini\antigravity-cli\brain\9636c74e-aff5-42a5-9d64-ac57f0c413c3"
    if os.path.exists(art_dir):
        shutil.copyfile(f1, os.path.join(art_dir, f1))
        shutil.copyfile(f2, os.path.join(art_dir, f2))

    print(f"✅ Successfully generated updated macro intelligence reports: {f1} & {f2} ({len(html_content)} bytes).")
    return True

if __name__ == "__main__":
    build_report()
