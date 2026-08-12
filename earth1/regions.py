"""Sub-national regional identity profiles — the Grounding Stack's regional layer.

Each region carries historical influence strata, economic specialization,
geographic character, and force deltas that modulate an agent's national
baseline. This is what makes a Sicilian different from a Milanese — same
country, different soul.

Coverage tiers:
  Tier 1 — top 30 countries: 5-12 hand-authored regions each
  Tier 2 — next 70 countries: 3-5 template-derived regions
  Tier 3 — remaining 94 small countries: 1 region = country itself
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math


@dataclass(frozen=True)
class RegionalProfile:
    code: str
    name: str
    country: str
    population_share: float
    historical_layers: Tuple[str, ...]
    economic_type: str
    economic_detail: str
    geographic_type: str
    force_deltas: Dict[str, float] = field(default_factory=dict)


def _r(code, name, country, pop, history, econ_type, econ_detail, geo, deltas=None):
    return RegionalProfile(
        code=code, name=name, country=country,
        population_share=pop,
        historical_layers=tuple(history),
        economic_type=econ_type, economic_detail=econ_detail,
        geographic_type=geo,
        force_deltas=deltas or {},
    )


# ── TIER 1: Hand-authored profiles (top 30 countries by population) ──

_TIER1 = [
    # ── INDIA ──
    _r("IN-NOR", "North India", "IN", 0.35,
       ["Vedic civilization", "Mughal Empire", "British Raj", "Partition", "Republic"],
       "mixed", "agriculture & services", "plains",
       {"collective": 0.06, "identity": 0.04, "culture": 0.05}),
    _r("IN-SOU", "South India", "IN", 0.25,
       ["Dravidian kingdoms", "Chola maritime", "Vijayanagara", "Colonial trading posts", "Republic"],
       "services", "IT & education hub", "coastal",
       {"identity": 0.06, "culture": 0.08, "economics": 0.04}),
    _r("IN-WES", "West India", "IN", 0.20,
       ["Maratha Empire", "Portuguese Goa", "British Bombay", "Republic"],
       "mixed", "finance & Bollywood & textiles", "coastal",
       {"economics": 0.06, "temperament": 0.04}),
    _r("IN-EAS", "East India", "IN", 0.12,
       ["Maurya Empire", "Pala dynasty", "Bengal Sultanate", "British Bengal", "Republic"],
       "agriculture", "rice & jute & tea", "plains",
       {"collective": 0.04, "fear": 0.03}),
    _r("IN-NEA", "Northeast India", "IN", 0.08,
       ["Ahom kingdom", "Tribal autonomy", "British annexation", "Republic"],
       "agriculture", "tea & bamboo & spices", "mountain",
       {"identity": 0.08, "culture": 0.06, "collective": -0.04}),

    # ── CHINA ──
    _r("CN-EAS", "East Coast", "CN", 0.30,
       ["Ancient dynasties", "Treaty ports", "Republican era", "Special Economic Zones"],
       "industry", "tech & manufacturing & finance", "coastal",
       {"economics": 0.08, "temperament": 0.04, "collective": -0.04}),
    _r("CN-NOR", "North China", "CN", 0.25,
       ["Imperial capitals", "Manchuria", "Japanese occupation", "Heavy industry era"],
       "industry", "heavy industry & state enterprises", "plains",
       {"collective": 0.08, "fear": 0.03, "economics": -0.03}),
    _r("CN-SOU", "South China", "CN", 0.25,
       ["Cantonese trade", "Opium Wars", "Republican revolution", "Reform & opening"],
       "mixed", "trade & light manufacturing & food", "coastal",
       {"economics": 0.06, "culture": 0.06, "identity": 0.04}),
    _r("CN-WES", "Western China", "CN", 0.12,
       ["Silk Road", "Tibetan Empire", "Qing expansion", "Development campaigns"],
       "agriculture", "pastoral & mining & tourism", "mountain",
       {"identity": 0.08, "culture": 0.10, "economics": -0.06}),
    _r("CN-CEN", "Central China", "CN", 0.08,
       ["Three Kingdoms", "Wuhan revolution", "Agricultural heartland"],
       "agriculture", "rice & grain basket", "plains",
       {"collective": 0.04, "economics": -0.02}),

    # ── UNITED STATES ──
    _r("US-NE", "Northeast", "US", 0.17,
       ["Colonial founding", "American Revolution", "Immigration waves", "Industrial revolution"],
       "services", "finance & education & media", "coastal",
       {"economics": 0.06, "identity": 0.04, "culture": 0.04}),
    _r("US-SE", "Southeast", "US", 0.20,
       ["Colonial plantations", "Civil War", "Reconstruction", "Civil Rights movement"],
       "mixed", "agriculture & military & growing tech", "coastal",
       {"collective": 0.08, "culture": 0.06, "identity": 0.06}),
    _r("US-MW", "Midwest", "US", 0.20,
       ["Frontier settlement", "Agricultural expansion", "Industrial heartland", "Rust Belt"],
       "mixed", "agriculture & manufacturing", "plains",
       {"collective": 0.06, "economics": -0.02}),
    _r("US-SW", "Southwest", "US", 0.15,
       ["Native American civilizations", "Spanish colonization", "Mexican-American War", "Sun Belt growth"],
       "mixed", "tech & energy & tourism", "desert",
       {"identity": 0.06, "culture": 0.08, "temperament": 0.04}),
    _r("US-WE", "West Coast", "US", 0.15,
       ["Gold Rush", "Asian immigration", "Tech revolution", "Entertainment industry"],
       "services", "tech & entertainment & trade", "coastal",
       {"temperament": 0.06, "economics": 0.06, "identity": 0.04}),
    _r("US-MR", "Mountain/Rural", "US", 0.13,
       ["Frontier expansion", "Mining booms", "Ranching culture", "Federal lands"],
       "extractive", "mining & ranching & energy", "mountain",
       {"identity": 0.08, "collective": -0.06, "temperament": 0.06}),

    # ── INDONESIA ──
    _r("ID-JAV", "Java", "ID", 0.55,
       ["Hindu-Buddhist kingdoms", "Majapahit", "Islamic sultanates", "Dutch East Indies", "Republic"],
       "industry", "manufacturing & services & agriculture", "island",
       {"collective": 0.06, "culture": 0.08}),
    _r("ID-SUM", "Sumatra", "ID", 0.22,
       ["Srivijaya maritime", "Aceh Sultanate", "Dutch colonization", "Oil boom"],
       "extractive", "palm oil & petroleum & rubber", "island",
       {"identity": 0.06, "economics": 0.04}),
    _r("ID-KAL", "Kalimantan", "ID", 0.07,
       ["Dayak indigenous", "Malay sultanates", "Dutch Borneo", "Resource extraction"],
       "extractive", "timber & mining & palm oil", "tropical",
       {"identity": 0.04, "economics": -0.04}),
    _r("ID-SUL", "Sulawesi & Eastern", "ID", 0.16,
       ["Bugis seafaring", "Spice trade", "Portuguese & Dutch", "Republic"],
       "mixed", "fishing & spices & nickel", "island",
       {"culture": 0.06, "identity": 0.04}),

    # ── PAKISTAN ──
    _r("PK-PUN", "Punjab", "PK", 0.53,
       ["Indus Valley", "Sikh Empire", "British Punjab", "Partition", "Green Revolution"],
       "agriculture", "wheat & cotton & textiles", "plains",
       {"collective": 0.06, "economics": 0.04}),
    _r("PK-SIN", "Sindh", "PK", 0.23,
       ["Indus civilization", "Arab conquest", "Mughal", "British", "Partition migration"],
       "mixed", "agriculture & Karachi port", "plains",
       {"economics": 0.06, "culture": 0.06}),
    _r("PK-KPB", "Khyber Pakhtunkhwa & Balochistan", "PK", 0.24,
       ["Alexander's campaign", "Gandharan Buddhism", "Afghan frontier", "Tribal autonomy"],
       "agriculture", "pastoral & mining", "mountain",
       {"identity": 0.10, "collective": 0.08, "fear": 0.06}),

    # ── NIGERIA ──
    _r("NG-NOR", "Northern Nigeria", "NG", 0.45,
       ["Hausa city-states", "Sokoto Caliphate", "British indirect rule", "Republic"],
       "agriculture", "grains & livestock & cotton", "plains",
       {"collective": 0.10, "identity": 0.06, "culture": 0.08}),
    _r("NG-SWE", "Southwest Nigeria", "NG", 0.25,
       ["Yoruba kingdoms", "Oyo Empire", "British Lagos colony", "Republic"],
       "services", "Lagos commerce & Nollywood", "coastal",
       {"economics": 0.06, "culture": 0.06, "temperament": 0.04}),
    _r("NG-SEA", "Southeast Nigeria", "NG", 0.20,
       ["Igbo civilization", "Slave trade impact", "Biafra War", "Republic"],
       "mixed", "trade & oil services", "tropical",
       {"identity": 0.08, "economics": 0.04, "fear": 0.04}),
    _r("NG-SSD", "South-South/Delta", "NG", 0.10,
       ["Niger Delta kingdoms", "Oil discovery", "Environmental conflict"],
       "extractive", "petroleum & gas", "coastal",
       {"economics": 0.06, "fear": 0.06}),

    # ── BRAZIL ──
    _r("BR-SE", "Southeast Brazil", "BR", 0.42,
       ["Portuguese colonization", "Coffee economy", "Industrialization", "Immigration waves"],
       "industry", "finance & manufacturing & coffee", "coastal",
       {"economics": 0.08, "culture": 0.04}),
    _r("BR-NE", "Northeast Brazil", "BR", 0.27,
       ["Sugar plantations", "African slave trade", "Drought cycles", "Cultural heartland"],
       "agriculture", "sugar & tourism & culture", "coastal",
       {"culture": 0.10, "identity": 0.06, "economics": -0.06}),
    _r("BR-SO", "South Brazil", "BR", 0.14,
       ["Jesuit missions", "European immigration", "Gaucho culture", "Agribusiness"],
       "agriculture", "soy & cattle & wine", "plains",
       {"economics": 0.04, "collective": 0.04}),
    _r("BR-NO", "North/Amazon", "BR", 0.09,
       ["Indigenous civilizations", "Rubber boom", "Environmental frontier"],
       "extractive", "timber & mining & river economy", "tropical",
       {"identity": 0.06, "culture": 0.08, "economics": -0.08}),
    _r("BR-CO", "Central-West", "BR", 0.08,
       ["Bandeirantes exploration", "Brasilia construction", "Cerrado agriculture"],
       "agriculture", "soy & cattle & government", "plains",
       {"temperament": 0.04}),

    # ── BANGLADESH ──
    _r("BD-DHK", "Dhaka Division", "BD", 0.35,
       ["Mughal province", "British Bengal", "Partition", "Liberation War", "Garment boom"],
       "industry", "garments & urban services", "plains",
       {"economics": 0.06, "collective": 0.04}),
    _r("BD-CHT", "Chittagong & Southeast", "BD", 0.25,
       ["Buddhist hill tracts", "Arab trade", "British port", "Liberation War"],
       "mixed", "port trade & tea & hill agriculture", "coastal",
       {"identity": 0.04, "culture": 0.06}),
    _r("BD-RAJ", "Rajshahi & Northwest", "BD", 0.25,
       ["Pala Buddhist dynasty", "Bengal Sultanate", "British era"],
       "agriculture", "rice & silk & mango", "plains",
       {"collective": 0.06}),
    _r("BD-KHU", "Khulna & Southwest", "BD", 0.15,
       ["Sundarbans", "Colonial era", "Climate vulnerability"],
       "agriculture", "shrimp & rice & mangrove", "coastal",
       {"fear": 0.06, "collective": 0.04}),

    # ── RUSSIA ──
    _r("RU-MOS", "Moscow & Central", "RU", 0.30,
       ["Muscovy", "Imperial capital", "Soviet center", "Post-Soviet transformation"],
       "services", "government & finance & media", "plains",
       {"economics": 0.08, "collective": 0.04}),
    _r("RU-SPB", "St. Petersburg & Northwest", "RU", 0.12,
       ["Peter's window to Europe", "Imperial culture", "Siege of Leningrad"],
       "services", "culture & education & port", "coastal",
       {"culture": 0.08, "identity": 0.04}),
    _r("RU-SIB", "Siberia", "RU", 0.15,
       ["Cossack expansion", "Exile & labor camps", "Resource frontier"],
       "extractive", "oil & gas & timber & mining", "mountain",
       {"temperament": 0.06, "identity": 0.04, "economics": 0.04}),
    _r("RU-URF", "Urals & Volga", "RU", 0.25,
       ["Tatar Khanate", "Industrial Urals", "Soviet heavy industry"],
       "industry", "metallurgy & machinery & oil", "mountain",
       {"collective": 0.06, "economics": 0.04}),
    _r("RU-SOU", "Southern Russia & Caucasus", "RU", 0.18,
       ["Cossack frontier", "Caucasus wars", "Soviet agricultural belt"],
       "agriculture", "grains & wine & pastoral", "mountain",
       {"identity": 0.08, "collective": 0.06, "culture": 0.06}),

    # ── MEXICO ──
    _r("MX-CEN", "Central Mexico", "MX", 0.35,
       ["Aztec Empire", "Spanish conquest", "Colonial capital", "Revolution", "NAFTA era"],
       "services", "government & services & industry", "mountain",
       {"collective": 0.04, "culture": 0.08}),
    _r("MX-NOR", "Northern Mexico", "MX", 0.25,
       ["Frontier territory", "Mining colonial", "Revolution birthplace", "Maquiladora industry"],
       "industry", "manufacturing & mining & ranching", "desert",
       {"temperament": 0.06, "economics": 0.06, "identity": 0.04}),
    _r("MX-SOU", "Southern Mexico", "MX", 0.20,
       ["Maya civilization", "Spanish missions", "Zapatista movement"],
       "agriculture", "coffee & corn & tourism", "tropical",
       {"identity": 0.08, "culture": 0.10, "economics": -0.06}),
    _r("MX-PAC", "Pacific & Bajío", "MX", 0.20,
       ["Pre-Columbian cultures", "Colonial silver mining", "Agricultural heartland"],
       "agriculture", "agave & agriculture & tourism", "coastal",
       {"culture": 0.06}),

    # ── JAPAN ──
    _r("JP-KAN", "Kanto (Tokyo)", "JP", 0.35,
       ["Edo period capital", "Meiji modernization", "Postwar economic miracle"],
       "services", "finance & tech & government", "coastal",
       {"economics": 0.08, "temperament": 0.04}),
    _r("JP-KNS", "Kansai (Osaka/Kyoto)", "JP", 0.20,
       ["Imperial capital", "Merchant culture", "Buddhist heritage"],
       "mixed", "commerce & tourism & manufacturing", "coastal",
       {"culture": 0.10, "economics": 0.04}),
    _r("JP-CHU", "Chubu & Hokuriku", "JP", 0.15,
       ["Mountain domains", "Silk & craft tradition", "Toyota industrial belt"],
       "industry", "automotive & manufacturing", "mountain",
       {"collective": 0.04, "economics": 0.04}),
    _r("JP-TOH", "Tohoku & Hokkaido", "JP", 0.15,
       ["Ainu indigenous", "Frontier settlement", "Agricultural north", "2011 disaster"],
       "agriculture", "rice & fishing & dairy", "coastal",
       {"collective": 0.06, "identity": 0.04, "fear": 0.04}),
    _r("JP-KYU", "Kyushu & Shikoku", "JP", 0.15,
       ["First European contact", "Christian persecution", "Volcanic geography"],
       "mixed", "agriculture & tech & ceramics", "island",
       {"culture": 0.06, "identity": 0.04}),

    # ── ETHIOPIA ──
    _r("ET-AMH", "Amhara & Tigray", "ET", 0.35,
       ["Aksumite Empire", "Ethiopian Orthodox", "Imperial dynasty", "Recent conflict"],
       "agriculture", "teff & coffee origin", "mountain",
       {"identity": 0.10, "culture": 0.08, "fear": 0.06}),
    _r("ET-ORO", "Oromia", "ET", 0.35,
       ["Oromo expansion", "Imperial incorporation", "Resistance movements"],
       "agriculture", "coffee & grains & livestock", "plains",
       {"identity": 0.08, "collective": 0.06}),
    _r("ET-SOU", "Southern Nations", "ET", 0.20,
       ["Diverse ethnic groups", "Imperial periphery", "Agricultural diversity"],
       "agriculture", "enset & coffee & spices", "mountain",
       {"culture": 0.08, "identity": 0.06}),
    _r("ET-SOM", "Somali & Afar", "ET", 0.10,
       ["Pastoral nomadic", "Colonial partition", "Clan systems"],
       "agriculture", "pastoral & trade", "desert",
       {"identity": 0.10, "collective": 0.08, "economics": -0.06}),

    # ── EGYPT ──
    _r("EG-CAI", "Greater Cairo", "EG", 0.30,
       ["Ancient Memphis", "Islamic conquest", "Mamluk", "Ottoman", "Modern capital"],
       "services", "government & commerce & media", "plains",
       {"economics": 0.06, "collective": 0.04}),
    _r("EG-NIL", "Nile Delta & Valley", "EG", 0.45,
       ["Pharaonic agriculture", "Roman breadbasket", "Arab settlement"],
       "agriculture", "cotton & rice & sugarcane", "plains",
       {"collective": 0.08, "culture": 0.06}),
    _r("EG-SIN", "Sinai & Red Sea", "EG", 0.10,
       ["Biblical crossroads", "Bedouin tribes", "1967 & 1973 wars", "Tourism"],
       "services", "tourism & mining", "desert",
       {"identity": 0.06, "fear": 0.06}),
    _r("EG-UPE", "Upper Egypt", "EG", 0.15,
       ["Ancient Thebes", "Coptic heritage", "Rural tradition"],
       "agriculture", "sugarcane & tourism", "desert",
       {"culture": 0.10, "collective": 0.08, "economics": -0.06}),

    # ── GERMANY ──
    _r("DE-NOR", "Northern Germany", "DE", 0.20,
       ["Hanseatic League", "Protestant Reformation", "Prussian influence", "Reunification"],
       "services", "ports & trade & wind energy", "coastal",
       {"economics": 0.04, "identity": 0.04}),
    _r("DE-NRW", "North Rhine-Westphalia", "DE", 0.22,
       ["Holy Roman Empire", "Industrial Ruhr", "Postwar reconstruction"],
       "industry", "heavy industry & chemicals & media", "plains",
       {"collective": 0.04, "economics": 0.06}),
    _r("DE-BAV", "Bavaria", "DE", 0.16,
       ["Wittelsbach dynasty", "Catholic tradition", "Postwar tech boom"],
       "industry", "automotive & tech & brewing", "mountain",
       {"culture": 0.08, "identity": 0.06, "collective": 0.04}),
    _r("DE-BW", "Baden-Württemberg", "DE", 0.14,
       ["Swabian tradition", "Engineering heritage", "Mittelstand"],
       "industry", "automotive & precision engineering", "mountain",
       {"economics": 0.06, "temperament": 0.04}),
    _r("DE-EAS", "Eastern Germany", "DE", 0.18,
       ["Prussian heartland", "DDR/Soviet occupation", "Reunification", "AfD support"],
       "mixed", "recovering industry & services", "plains",
       {"collective": 0.06, "fear": 0.06, "economics": -0.04}),
    _r("DE-BER", "Berlin", "DE", 0.10,
       ["Prussian capital", "Weimar culture", "Division & Wall", "Reunification & creative boom"],
       "services", "government & tech & culture", "plains",
       {"identity": 0.06, "culture": 0.08, "temperament": 0.06}),

    # ── FRANCE ──
    _r("FR-IDF", "Île-de-France (Paris)", "FR", 0.19,
       ["Medieval capital", "Revolution", "Haussmann", "Republic"],
       "services", "finance & fashion & government", "plains",
       {"economics": 0.08, "culture": 0.06}),
    _r("FR-SOU", "South/Mediterranean", "FR", 0.22,
       ["Roman Provincia", "Occitan culture", "Tourism & agriculture"],
       "mixed", "wine & tourism & tech (Sophia Antipolis)", "coastal",
       {"culture": 0.08, "temperament": 0.04}),
    _r("FR-NOR", "North & East", "FR", 0.20,
       ["Frankish kingdoms", "Industrial revolution", "WWI battlefields"],
       "industry", "manufacturing & mining (legacy)", "plains",
       {"collective": 0.06, "economics": -0.04}),
    _r("FR-OUE", "West/Atlantic", "FR", 0.22,
       ["Breton Celtic", "Atlantic trade", "Agricultural France"],
       "agriculture", "dairy & seafood & tourism", "coastal",
       {"identity": 0.04, "culture": 0.06}),
    _r("FR-RHA", "Rhône-Alpes & Central", "FR", 0.17,
       ["Burgundian heritage", "Lyon silk trade", "Alpine economy"],
       "mixed", "pharma & food & winter sports", "mountain",
       {"economics": 0.04}),

    # ── UNITED KINGDOM ──
    _r("GB-LON", "London & Southeast", "GB", 0.28,
       ["Roman Londinium", "Medieval commerce", "Empire capital", "Global finance"],
       "services", "finance & tech & media & government", "plains",
       {"economics": 0.10, "culture": 0.04}),
    _r("GB-MID", "Midlands & North England", "GB", 0.28,
       ["Industrial Revolution", "Coal & steel", "Deindustrialization", "Levelling Up"],
       "mixed", "legacy industry & services", "plains",
       {"collective": 0.06, "economics": -0.04, "identity": 0.04}),
    _r("GB-SCO", "Scotland", "GB", 0.08,
       ["Celtic kingdoms", "Scottish Enlightenment", "Union", "Devolution"],
       "mixed", "oil & whisky & finance & tech", "mountain",
       {"identity": 0.10, "culture": 0.06}),
    _r("GB-WAL", "Wales", "GB", 0.05,
       ["Celtic Britons", "Coal mining", "Deindustrialization", "Devolution"],
       "mixed", "services & legacy mining", "mountain",
       {"identity": 0.08, "collective": 0.06, "economics": -0.04}),
    _r("GB-SW", "Southwest & East Anglia", "GB", 0.21,
       ["Anglo-Saxon kingdoms", "Naval heritage", "Agricultural England"],
       "mixed", "agriculture & tourism & aerospace", "coastal",
       {"culture": 0.04}),
    _r("GB-NIR", "Northern Ireland", "GB", 0.10,
       ["Ulster Plantation", "Partition", "The Troubles", "Peace Process"],
       "mixed", "services & agriculture", "coastal",
       {"identity": 0.10, "collective": 0.08, "fear": 0.06}),

    # ── ITALY ──
    _r("IT-NW", "Northwest Italy", "IT", 0.25,
       ["Roman Cisalpina", "Medieval communes", "Industrial triangle", "Immigration hub"],
       "industry", "automotive & fashion & finance", "plains",
       {"economics": 0.08, "temperament": 0.04}),
    _r("IT-NE", "Northeast Italy", "IT", 0.18,
       ["Venetian Republic", "Austrian Empire", "Small enterprise miracle"],
       "industry", "SME manufacturing & wine & tourism", "coastal",
       {"economics": 0.06, "culture": 0.06, "collective": 0.04}),
    _r("IT-CEN", "Central Italy", "IT", 0.18,
       ["Etruscan civilization", "Roman Republic", "Renaissance Florence", "Papal States"],
       "mixed", "tourism & food & artisan & government", "mountain",
       {"culture": 0.12, "identity": 0.04}),
    _r("IT-SOU", "Southern Italy (Mezzogiorno)", "IT", 0.22,
       ["Magna Graecia", "Norman Kingdom", "Spanish Crown", "Bourbon Kingdom", "Unification gap"],
       "agriculture", "agriculture & tourism", "coastal",
       {"collective": 0.08, "culture": 0.08, "economics": -0.06, "identity": 0.06}),
    _r("IT-SIC", "Sicily", "IT", 0.08,
       ["Greek colonization", "Roman granary", "Arab Emirate", "Norman Kingdom",
        "Spanish Crown", "Bourbon Kingdom", "Fascist era", "Italian Republic"],
       "agriculture", "olive oil & citrus & wine & fishing", "island",
       {"collective": 0.08, "identity": 0.06, "culture": 0.10, "fear": 0.04, "economics": -0.05}),
    _r("IT-SAR", "Sardinia", "IT", 0.09,
       ["Nuragic civilization", "Phoenician", "Roman", "Spanish", "Savoy"],
       "mixed", "pastoral & tourism & mining", "island",
       {"identity": 0.08, "culture": 0.06, "collective": 0.04}),

    # ── SOUTH KOREA ──
    _r("KR-SEO", "Seoul Metropolitan", "KR", 0.50,
       ["Joseon capital", "Japanese occupation", "Korean War", "Economic miracle", "K-wave"],
       "services", "tech & finance & entertainment", "plains",
       {"economics": 0.10, "temperament": 0.06}),
    _r("KR-GYE", "Gyeongsang (Southeast)", "KR", 0.25,
       ["Silla kingdom", "Japanese colonial industry", "Park Chung-hee industrialization"],
       "industry", "shipbuilding & steel & automotive", "coastal",
       {"collective": 0.06, "economics": 0.04}),
    _r("KR-JEO", "Jeolla (Southwest)", "KR", 0.15,
       ["Baekje kingdom", "Rice granary", "1980 Gwangju uprising"],
       "agriculture", "rice & food culture", "plains",
       {"identity": 0.08, "culture": 0.06}),
    _r("KR-GAN", "Gangwon & Jeju", "KR", 0.10,
       ["Mountain frontier", "Korean War front", "Tourism development"],
       "services", "tourism & agriculture", "mountain",
       {"culture": 0.04}),

    # ── TURKEY ──
    _r("TR-MAR", "Marmara (Istanbul)", "TR", 0.30,
       ["Byzantine Empire", "Ottoman capital", "Republic", "EU gateway"],
       "services", "finance & trade & industry", "coastal",
       {"economics": 0.08, "culture": 0.06}),
    _r("TR-AEG", "Aegean & Mediterranean", "TR", 0.20,
       ["Ancient Ionia", "Hellenistic", "Ottoman", "Tourism belt"],
       "services", "tourism & agriculture & olive oil", "coastal",
       {"culture": 0.06, "temperament": 0.04}),
    _r("TR-ANA", "Central Anatolia", "TR", 0.20,
       ["Hittites", "Seljuk Turks", "Ottoman heartland", "Ankara capital"],
       "mixed", "government & agriculture & industry", "plains",
       {"collective": 0.06, "identity": 0.04}),
    _r("TR-BLA", "Black Sea", "TR", 0.10,
       ["Pontus kingdom", "Tea & hazelnut culture", "Mountain isolation"],
       "agriculture", "tea & hazelnuts & fishing", "mountain",
       {"identity": 0.06, "collective": 0.06}),
    _r("TR-EAS", "Eastern Turkey", "TR", 0.20,
       ["Armenian kingdoms", "Kurdish homeland", "Ottoman frontier", "Conflict zone"],
       "agriculture", "pastoral & agriculture", "mountain",
       {"identity": 0.10, "collective": 0.08, "fear": 0.06, "economics": -0.06}),

    # ── THAILAND ──
    _r("TH-BKK", "Bangkok Metropolitan", "TH", 0.20,
       ["Ayutthaya successor", "Chakri dynasty", "Modernization", "Economic hub"],
       "services", "finance & tourism & manufacturing", "plains",
       {"economics": 0.08}),
    _r("TH-NOR", "Northern Thailand", "TH", 0.18,
       ["Lanna Kingdom", "Teak trade", "Hill tribes", "Tourism"],
       "mixed", "agriculture & tourism & crafts", "mountain",
       {"culture": 0.08, "identity": 0.06}),
    _r("TH-NE", "Isan (Northeast)", "TH", 0.35,
       ["Khmer influence", "Lao cultural ties", "Agricultural plateau", "Migration to Bangkok"],
       "agriculture", "rice & cassava & silk", "plains",
       {"collective": 0.06, "economics": -0.06, "culture": 0.06}),
    _r("TH-SOU", "Southern Thailand", "TH", 0.17,
       ["Malay sultanates", "Tin mining", "Rubber & tourism", "Border conflict"],
       "mixed", "rubber & fishing & tourism", "coastal",
       {"identity": 0.06, "fear": 0.04}),
    _r("TH-CEN", "Central Plains", "TH", 0.10,
       ["Rice bowl", "Ayutthaya heritage", "Agricultural heartland"],
       "agriculture", "rice & sugar", "plains",
       {"collective": 0.04}),

    # ── SOUTH AFRICA ──
    _r("ZA-GAU", "Gauteng", "ZA", 0.27,
       ["Gold Rush", "Apartheid capital", "Post-apartheid transformation"],
       "services", "finance & mining HQ & tech", "plains",
       {"economics": 0.08, "identity": 0.06}),
    _r("ZA-WCA", "Western Cape", "ZA", 0.12,
       ["Dutch settlement", "British colony", "Wine culture", "Tech hub"],
       "services", "tourism & wine & tech", "coastal",
       {"culture": 0.06, "economics": 0.04}),
    _r("ZA-KZN", "KwaZulu-Natal", "ZA", 0.20,
       ["Zulu Kingdom", "British Natal colony", "Indian immigration", "Apartheid"],
       "mixed", "sugar & tourism & port", "coastal",
       {"identity": 0.08, "collective": 0.06, "culture": 0.06}),
    _r("ZA-ECA", "Eastern Cape", "ZA", 0.12,
       ["Xhosa homeland", "Frontier wars", "Anti-apartheid leaders birthplace"],
       "mixed", "automotive & agriculture", "coastal",
       {"identity": 0.08, "collective": 0.06, "economics": -0.06}),
    _r("ZA-OTH", "Other Provinces", "ZA", 0.29,
       ["Mining belt", "Agricultural interior", "Post-apartheid development"],
       "mixed", "mining & agriculture", "plains",
       {"collective": 0.04}),

    # ── PHILIPPINES ──
    _r("PH-NCR", "Metro Manila", "PH", 0.13,
       ["Spanish colonial capital", "American period", "Marcos era", "EDSA revolution"],
       "services", "BPO & government & finance", "coastal",
       {"economics": 0.08}),
    _r("PH-LUZ", "Luzon (outside NCR)", "PH", 0.40,
       ["Ilocos & Cordillera indigenous", "Spanish missions", "Agricultural lowlands"],
       "agriculture", "rice & tobacco & vegetables", "mountain",
       {"collective": 0.06, "culture": 0.04}),
    _r("PH-VIS", "Visayas", "PH", 0.22,
       ["Magellan's landing", "Spanish colonial heartland", "Cebu commerce"],
       "mixed", "tourism & agriculture & shipping", "island",
       {"culture": 0.06, "identity": 0.04}),
    _r("PH-MIN", "Mindanao", "PH", 0.25,
       ["Moro Sultanates", "American & Japanese period", "MILF/MNLF conflict", "Bangsamoro"],
       "agriculture", "banana & pineapple & fishing", "island",
       {"identity": 0.10, "fear": 0.06, "collective": 0.06}),

    # ── VIETNAM ──
    _r("VN-NOR", "Northern Vietnam", "VN", 0.35,
       ["Chinese millennium", "Dai Viet independence", "French Indochina", "Ho Chi Minh", "Doi Moi"],
       "industry", "manufacturing & government", "plains",
       {"collective": 0.08, "culture": 0.06}),
    _r("VN-CEN", "Central Vietnam", "VN", 0.20,
       ["Champa kingdom", "Hue imperial capital", "DMZ & war", "Heritage tourism"],
       "mixed", "tourism & fishing & agriculture", "coastal",
       {"culture": 0.08, "identity": 0.04, "fear": 0.04}),
    _r("VN-SOU", "Southern Vietnam", "VN", 0.45,
       ["Khmer influence", "Nguyen lords", "French Cochinchina", "Saigon/HCMC boom"],
       "mixed", "commerce & agriculture & manufacturing", "plains",
       {"economics": 0.08, "temperament": 0.04}),

    # ── SPAIN ──
    _r("ES-MAD", "Madrid & Central", "ES", 0.20,
       ["Reconquista", "Habsburg capital", "Civil War", "Democratic transition"],
       "services", "government & finance", "plains",
       {"economics": 0.04}),
    _r("ES-CAT", "Catalonia", "ES", 0.16,
       ["County of Barcelona", "Crown of Aragon", "Industrial revolution", "Independence movement"],
       "industry", "manufacturing & tourism & tech", "coastal",
       {"identity": 0.10, "economics": 0.06, "culture": 0.06}),
    _r("ES-AND", "Andalusia", "ES", 0.18,
       ["Phoenician", "Roman Baetica", "Umayyad Caliphate", "Reconquista", "Agrarian south"],
       "agriculture", "olive oil & tourism & agriculture", "coastal",
       {"culture": 0.12, "collective": 0.06, "economics": -0.04}),
    _r("ES-BAQ", "Basque Country", "ES", 0.05,
       ["Pre-Indo-European people", "Medieval autonomy", "Industrialization", "ETA era", "Self-governance"],
       "industry", "steel & cooperatives & gastronomy", "mountain",
       {"identity": 0.12, "collective": 0.06, "economics": 0.06}),
    _r("ES-VAL", "Valencia & Mediterranean", "ES", 0.18,
       ["Roman Valentia", "Moorish irrigation", "Silk & ceramics", "Tourism boom"],
       "mixed", "agriculture & tourism & ceramics", "coastal",
       {"culture": 0.06, "temperament": 0.04}),
    _r("ES-NW", "Galicia & Northwest", "ES", 0.10,
       ["Celtic heritage", "Santiago pilgrimage", "Maritime culture"],
       "mixed", "fishing & agriculture & tourism", "coastal",
       {"culture": 0.08, "identity": 0.06}),
    _r("ES-ISL", "Canaries & Balearics", "ES", 0.13,
       ["Guanche indigenous", "Spanish colonization", "Tourism economy"],
       "services", "tourism & agriculture", "island",
       {"culture": 0.04, "economics": 0.04}),

    # ── COLOMBIA ──
    _r("CO-AND", "Andean Region", "CO", 0.55,
       ["Muisca civilization", "Spanish colonial", "Coffee axis", "Bogota urbanization"],
       "mixed", "coffee & flowers & services", "mountain",
       {"culture": 0.06, "collective": 0.04}),
    _r("CO-CAR", "Caribbean Coast", "CO", 0.20,
       ["Cartagena fortress", "African heritage", "Vallenato culture"],
       "mixed", "tourism & port & agriculture", "coastal",
       {"culture": 0.08, "temperament": 0.06}),
    _r("CO-PAC", "Pacific Coast", "CO", 0.10,
       ["Afro-Colombian heritage", "Mining & logging", "Conflict zone"],
       "extractive", "mining & fishing", "coastal",
       {"identity": 0.08, "fear": 0.06, "economics": -0.06}),
    _r("CO-ORI", "Orinoco & Amazon", "CO", 0.15,
       ["Indigenous territories", "Llanos cattle", "Oil & coca conflict"],
       "extractive", "oil & cattle & coca substitution", "tropical",
       {"identity": 0.06, "fear": 0.04}),

    # ── ARGENTINA ──
    _r("AR-BUE", "Buenos Aires", "AR", 0.40,
       ["Spanish viceroyalty", "European immigration", "Tango", "Peronism"],
       "services", "finance & culture & port", "coastal",
       {"economics": 0.06, "culture": 0.08}),
    _r("AR-PAM", "Pampas", "AR", 0.20,
       ["Gaucho frontier", "Agricultural boom", "Estancia culture"],
       "agriculture", "soy & cattle & wheat", "plains",
       {"economics": 0.04, "identity": 0.04}),
    _r("AR-NOR", "Northwest Argentina", "AR", 0.15,
       ["Inca expansion", "Spanish colonial", "Indigenous heritage"],
       "agriculture", "wine & mining & tourism", "mountain",
       {"culture": 0.08, "identity": 0.06, "economics": -0.04}),
    _r("AR-PAT", "Patagonia", "AR", 0.10,
       ["Mapuche & Tehuelche", "Welsh colonies", "Oil & sheep"],
       "extractive", "oil & gas & wool & tourism", "mountain",
       {"temperament": 0.06, "identity": 0.06}),
    _r("AR-NEA", "Northeast Argentina", "AR", 0.15,
       ["Guaraní heritage", "Jesuit missions", "Yerba mate culture"],
       "agriculture", "yerba mate & forestry & rice", "tropical",
       {"culture": 0.06, "collective": 0.04}),

    # ── POLAND ──
    _r("PL-MAZ", "Masovia (Warsaw)", "PL", 0.25,
       ["Piast dynasty", "Partitions", "Warsaw Uprising", "Communist capital", "EU accession"],
       "services", "government & finance & tech", "plains",
       {"economics": 0.06}),
    _r("PL-SIL", "Silesia & South", "PL", 0.25,
       ["Medieval mining", "Prussian/Austrian rule", "Heavy industry", "Transformation"],
       "industry", "mining & manufacturing", "mountain",
       {"collective": 0.06, "economics": 0.04}),
    _r("PL-GDA", "Pomerania (Gdańsk)", "PL", 0.15,
       ["Hanseatic League", "Prussian rule", "Solidarność birthplace"],
       "mixed", "port & shipbuilding & tourism", "coastal",
       {"identity": 0.06, "temperament": 0.04}),
    _r("PL-EAS", "Eastern Poland", "PL", 0.20,
       ["Multi-ethnic borderland", "Partitions", "Agricultural tradition"],
       "agriculture", "agriculture & forestry", "plains",
       {"collective": 0.06, "culture": 0.06, "economics": -0.04}),
    _r("PL-WES", "Greater Poland & West", "PL", 0.15,
       ["Piast cradle", "Prussian rule", "Postwar resettlement"],
       "mixed", "agriculture & manufacturing", "plains",
       {"economics": 0.04}),

    # ── KENYA ──
    _r("KE-NAI", "Nairobi & Central", "KE", 0.30,
       ["Kikuyu homeland", "British colonial capital", "Mau Mau", "Tech hub"],
       "services", "tech & finance & government", "mountain",
       {"economics": 0.08, "temperament": 0.04}),
    _r("KE-COA", "Coast (Mombasa)", "KE", 0.15,
       ["Swahili city-states", "Portuguese", "Omani", "British port"],
       "services", "tourism & port & trade", "coastal",
       {"culture": 0.08, "economics": 0.04}),
    _r("KE-RIF", "Rift Valley", "KE", 0.25,
       ["Maasai & Kalenjin", "Colonial settlers", "Agricultural highlands"],
       "agriculture", "tea & flowers & wheat", "mountain",
       {"identity": 0.06, "collective": 0.06}),
    _r("KE-WES", "Western & Nyanza", "KE", 0.20,
       ["Luo & Luhya", "Lake Victoria fishing", "Sugar belt"],
       "agriculture", "sugar & fishing & agriculture", "plains",
       {"collective": 0.06, "identity": 0.04}),
    _r("KE-NOR", "Northern Kenya", "KE", 0.10,
       ["Pastoral Somali & Turkana", "Colonial neglect", "Arid frontier"],
       "agriculture", "pastoral & emerging oil", "desert",
       {"identity": 0.08, "fear": 0.04, "economics": -0.06}),
]


# ── TIER 2: Template-derived profiles ──
# For countries ranked 31-100, generate 3 regions from archetypes

_ECONOMIC_ARCHETYPES = {
    "capital_urban": ("services", "government & commerce & services", {"economics": 0.06}),
    "agricultural_heartland": ("agriculture", "agriculture & primary sector", {"collective": 0.04}),
    "coastal_trading": ("mixed", "port & trade & fishing", {"economics": 0.04, "culture": 0.04}),
    "industrial_belt": ("industry", "manufacturing & industry", {"economics": 0.04, "collective": 0.04}),
    "resource_frontier": ("extractive", "mining & resource extraction", {"identity": 0.04, "economics": -0.02}),
    "cultural_heartland": ("mixed", "traditional culture & agriculture", {"culture": 0.08, "identity": 0.06}),
}

_GEO_ARCHETYPES = {
    "coastal": {"temperament": 0.02},
    "mountain": {"identity": 0.02, "collective": 0.02},
    "plains": {},
    "island": {"identity": 0.04, "culture": 0.04},
    "desert": {"collective": 0.04, "fear": 0.02},
    "tropical": {"culture": 0.02},
}


def _make_tier2(country_iso2, country_name, region_name):
    """Generate 3 template regions for a non-Tier-1 country."""
    profiles = []
    templates = [
        (f"{country_iso2}-CAP", f"{country_name} Capital Region", 0.35,
         ["Pre-colonial era", "Colonial period", "Independence", "Urbanization"],
         "capital_urban", "plains"),
        (f"{country_iso2}-RUR", f"{country_name} Rural Heartland", 0.40,
         ["Traditional settlement", "Colonial administration", "Post-independence"],
         "agricultural_heartland", "plains"),
        (f"{country_iso2}-PER", f"{country_name} Periphery", 0.25,
         ["Indigenous/pre-colonial", "Colonial frontier", "Post-independence periphery"],
         "resource_frontier", "mountain"),
    ]

    if region_name in ("Latin America", "Southeast Asia", "Sub-Saharan Africa",
                        "Middle East/N. Africa"):
        templates[2] = (
            f"{country_iso2}-PER", f"{country_name} Periphery", 0.25,
            ["Indigenous heritage", "Colonial frontier", "Modern development"],
            "cultural_heartland", "tropical" if region_name in (
                "Latin America", "Southeast Asia", "Sub-Saharan Africa") else "desert",
        )

    for code, name, pop, history, econ_key, geo in templates:
        econ_type, econ_detail, econ_deltas = _ECONOMIC_ARCHETYPES[econ_key]
        geo_deltas = _GEO_ARCHETYPES.get(geo, {})
        merged = {**econ_deltas, **geo_deltas}
        profiles.append(_r(code, name, country_iso2, pop,
                           history, econ_type, econ_detail, geo, merged))
    return profiles


# ── Build complete registry ──

_PROFILES_BY_COUNTRY: Dict[str, List[RegionalProfile]] = {}

for p in _TIER1:
    _PROFILES_BY_COUNTRY.setdefault(p.country, []).append(p)

# Tier 1 countries
_TIER1_COUNTRIES = set(_PROFILES_BY_COUNTRY.keys())

# Generate Tier 2 for countries 31-100 by population
from earth1.census import CENSUS_TARGETS
_TIER2_COUNTRIES = set()
for i, c in enumerate(CENSUS_TARGETS):
    iso2 = c["iso2"]
    if iso2 not in _TIER1_COUNTRIES and i < 100:
        profiles = _make_tier2(iso2, c["name"], c["region"])
        _PROFILES_BY_COUNTRY[iso2] = profiles
        _TIER2_COUNTRIES.add(iso2)

# Tier 3: remaining countries get single self-referencing profile
for c in CENSUS_TARGETS:
    iso2 = c["iso2"]
    if iso2 not in _PROFILES_BY_COUNTRY:
        _PROFILES_BY_COUNTRY[iso2] = [
            _r(iso2, c["name"], iso2, 1.0,
               ["Historical development"], "mixed", "national economy",
               "plains", {})
        ]


def get_regions(country_iso2: str) -> List[RegionalProfile]:
    return _PROFILES_BY_COUNTRY.get(country_iso2, [])


def get_region_by_code(region_code: str) -> Optional[RegionalProfile]:
    for profiles in _PROFILES_BY_COUNTRY.values():
        for p in profiles:
            if p.code == region_code:
                return p
    return None


def all_regions() -> List[RegionalProfile]:
    result = []
    for profiles in _PROFILES_BY_COUNTRY.values():
        result.extend(profiles)
    return result


def tier1_countries() -> List[str]:
    return sorted(_TIER1_COUNTRIES)


def tier2_countries() -> List[str]:
    return sorted(_TIER2_COUNTRIES)


def region_force_deltas(region_code: str) -> Dict[str, float]:
    """Get force deltas for a region. Returns empty dict if not found."""
    p = get_region_by_code(region_code)
    return dict(p.force_deltas) if p else {}


def sample_region(country_iso2: str, rng) -> RegionalProfile:
    """Sample a region within a country using population shares."""
    regions = get_regions(country_iso2)
    if not regions:
        raise ValueError(f"No regions for {country_iso2}")
    if len(regions) == 1:
        return regions[0]
    shares = [r.population_share for r in regions]
    total = sum(shares)
    shares = [s / total for s in shares]
    idx = rng.choice(len(regions), p=shares)
    return regions[idx]
