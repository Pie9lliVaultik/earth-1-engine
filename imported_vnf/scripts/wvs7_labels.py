"""
wvs7_labels.py — canonical wording for WVS Wave 7 master variables.

HOW THIS MAP WAS VALIDATED (not from memory alone)
--------------------------------------------------
Every raw column Q1..Q290 was aggregated per country from the microdata and
correlated against the 299 WVS items already in `benchmark_calibrations`
(sourced from the published GlobalOpinionQA bank, which carries the verbatim
questionnaire wording). 89 columns matched a published item at r > 0.90 and
mean-absolute-difference < 0.08 — including anchors spread across every block
(Q1-Q6 importance, Q9-Q17 child qualities, Q18-Q23 neighbours, Q28-Q32 gender,
Q57-Q63 trust, Q64/Q68/Q72/Q73/Q75/Q76/Q77/Q78/Q83/Q88 confidence,
Q133-Q141 neighbourhood safety, Q165-Q168 belief, Q196-Q198 surveillance,
Q199 political interest). Those hits pin the block offsets, so the labels for
the un-matched siblings inside an already-pinned block are safe.

Blocks that could NOT be pinned by at least one verified anchor, or where the
1..10 pole direction is ambiguous (Q106-Q111 economic scales, Q121-Q129
immigrant-impact, Q152-Q157 country aims, Q90-Q105 organisation membership
which uses a 0..2 code), are deliberately omitted. A wrong polarity is worse
than a missing item, so they stay out.

Format: code -> canonical short question text. The binarization rule is derived
from the observed value range in the microdata (see aggregate_wvs7_full.py):
  max 2   -> yes = (v == 1)          (mentioned / chose first option)
  max 3-5 -> yes = (v in (1, 2))     (top-two of an ordered scale, 1 = most)
  max 10  -> yes = (v between 6 and 10)
"""

LABELS: dict[str, str] = {}


def _add(items: dict[str, str]) -> None:
    LABELS.update(items)


# --- Importance in life (1 = very important) -------------------------------
_add({
    "Q1": "Is family important in your life?",
    "Q2": "Are friends important in your life?",
    "Q3": "Is leisure time important in your life?",
    "Q4": "Is politics important in your life?",
    "Q5": "Is work important in your life?",
    "Q6": "Is religion important in your life?",
})

# --- Qualities children should learn at home (1 = mentioned) ---------------
_add({
    "Q7": "Should children be encouraged to learn good manners at home?",
    "Q8": "Should children be encouraged to learn independence at home?",
    "Q9": "Should children be encouraged to learn hard work at home?",
    "Q10": "Should children be encouraged to learn a feeling of responsibility at home?",
    "Q11": "Should children be encouraged to learn imagination at home?",
    "Q12": "Should children be encouraged to learn tolerance and respect for other people?",
    "Q13": "Should children be encouraged to learn thrift, saving money and things?",
    "Q14": "Should children be encouraged to learn determination and perseverance?",
    "Q15": "Should children be encouraged to learn religious faith at home?",
    "Q16": "Should children be encouraged to learn unselfishness at home?",
    "Q17": "Should children be encouraged to learn obedience at home?",
})

# --- Groups you would not want as neighbours (1 = mentioned) ---------------
_add({
    "Q18": "Would you object to having drug addicts as neighbours?",
    "Q19": "Would you object to having people of a different race as neighbours?",
    "Q20": "Would you object to having people who have AIDS as neighbours?",
    "Q21": "Would you object to having immigrants or foreign workers as neighbours?",
    "Q22": "Would you object to having homosexuals as neighbours?",
    "Q23": "Would you object to having people of a different religion as neighbours?",
    "Q24": "Would you object to having heavy drinkers as neighbours?",
    "Q25": "Would you object to having unmarried couples living together as neighbours?",
    "Q26": "Would you object to having people who speak a different language as neighbours?",
})

# --- Family and gender attitudes (1 = agree strongly) ----------------------
_add({
    "Q27": "Has making your parents proud been one of your main goals in life?",
    "Q28": "Do children suffer when a mother works for pay?",
    "Q29": "Do men make better political leaders than women do?",
    "Q30": "Is a university education more important for a boy than for a girl?",
    "Q31": "Do men make better business executives than women do?",
    "Q32": "Is being a housewife just as fulfilling as working for pay?",
    "Q35": "Are homosexual couples as good parents as other couples?",
    "Q36": "Is it a duty towards society to have children?",
    "Q37": "Do adult children have a duty to provide long-term care for their parents?",
})

# --- Wellbeing (1 = very happy / very good health; 1..10 satisfaction) -----
_add({
    "Q46": "Are you happy, taking all things together?",
    "Q47": "Is your state of health good?",
    "Q48": "Do you feel you have a great deal of free choice and control over your life?",
    "Q49": "Are you satisfied with your life as a whole?",
    "Q50": "Are you satisfied with the financial situation of your household?",
})

# --- Material insecurity in the past year (1 = often) ----------------------
_add({
    "Q51": "In the past year, have you or your family gone without enough food to eat?",
    "Q52": "In the past year, have you or your family felt unsafe from crime in your own home?",
    "Q53": "In the past year, have you or your family gone without needed medicine or medical treatment?",
    "Q54": "In the past year, have you or your family gone without a cash income?",
    "Q55": "In the past year, have you or your family gone without a safe shelter over your head?",
})

# --- Trust (Q57 binary; Q58-Q63 1 = trust completely) ----------------------
_add({
    "Q57": "Can most people be trusted?",
    "Q58": "Do you trust your family?",
    "Q59": "Do you trust people in your neighbourhood?",
    "Q60": "Do you trust people you know personally?",
    "Q61": "Do you trust people you meet for the first time?",
    "Q62": "Do you trust people of another religion?",
    "Q63": "Do you trust people of another nationality?",
})

# --- Confidence in institutions (1 = a great deal) -------------------------
_add({
    "Q64": "Do you have confidence in the churches?",
    "Q65": "Do you have confidence in the armed forces?",
    "Q66": "Do you have confidence in the press?",
    "Q67": "Do you have confidence in television?",
    "Q68": "Do you have confidence in labour unions?",
    "Q69": "Do you have confidence in the police?",
    "Q70": "Do you have confidence in the courts?",
    "Q71": "Do you have confidence in the national government?",
    "Q72": "Do you have confidence in political parties?",
    "Q73": "Do you have confidence in parliament?",
    "Q74": "Do you have confidence in the civil service?",
    "Q75": "Do you have confidence in universities?",
    "Q76": "Do you have confidence in elections?",
    "Q77": "Do you have confidence in major companies?",
    "Q78": "Do you have confidence in banks?",
    "Q79": "Do you have confidence in environmental organizations?",
    "Q80": "Do you have confidence in women's organizations?",
    "Q81": "Do you have confidence in charitable or humanitarian organizations?",
    "Q83": "Do you have confidence in the United Nations?",
    "Q84": "Do you have confidence in the International Monetary Fund?",
    "Q85": "Do you have confidence in the International Criminal Court?",
    "Q86": "Do you have confidence in NATO?",
    "Q87": "Do you have confidence in the World Bank?",
    "Q88": "Do you have confidence in the World Health Organization?",
})

# --- Corruption perception (1 = all of them involved) ----------------------
_add({
    "Q113": "Are state authorities in your country involved in corruption?",
    "Q115": "Are local authorities in your country involved in corruption?",
    "Q117": "Are journalists and the media in your country involved in corruption?",
})

# --- Immigration policy (verified item) ------------------------------------
_add({
    "Q130": "Should the government let anyone come who wants to, rather than restrict immigration?",
})

# --- Neighbourhood conditions (1 = very frequently) ------------------------
_add({
    "Q132": "Do robberies occur frequently in your neighbourhood?",
    "Q133": "Is alcohol consumed in the streets in your neighbourhood?",
    "Q134": "Do police or the military interfere with people's private life in your neighbourhood?",
    "Q135": "Does racist behaviour occur in your neighbourhood?",
    "Q136": "Are drugs sold in the streets in your neighbourhood?",
    "Q137": "Do street violence and fights occur in your neighbourhood?",
    "Q138": "Does sexual harassment occur in your neighbourhood?",
})

# --- Security behaviour and victimhood -------------------------------------
_add({
    "Q141": "Have you carried a knife, gun or other weapon for reasons of security?",
    "Q144": "Have you been the victim of a crime during the past year?",
    "Q151": "Would you be willing to fight for your country in a war?",
})

# --- Science and technology (1..10, 6-10 = agree) --------------------------
_add({
    "Q158": "Does science and technology make our lives healthier, easier and more comfortable?",
    "Q159": "Does science and technology give the next generation more opportunities?",
    "Q160": "Does science make our way of life change too fast?",
    "Q161": "Do we depend too much on science and not enough on faith?",
    "Q163": "Is it important for you to know about science in your daily life?",
})

# --- Religion --------------------------------------------------------------
_add({
    "Q164": "Is God important in your life?",
    "Q165": "Do you believe in God?",
    "Q166": "Do you believe in life after death?",
    "Q167": "Do you believe in hell?",
    "Q168": "Do you believe in heaven?",
    "Q169": "Whenever science and religion conflict, is religion always right?",
    "Q170": "Is the only acceptable religion your religion?",
    "Q171": "Do you attend religious services regularly?",
    "Q172": "Do you pray regularly outside of religious services?",
    "Q173": "Are you a religious person?",
})

# --- Justifiability (1..10, 6-10 = justifiable) ----------------------------
_add({
    "Q177": "Is claiming government benefits you are not entitled to justifiable?",
    "Q178": "Is avoiding a fare on public transport justifiable?",
    "Q179": "Is stealing property justifiable?",
    "Q180": "Is cheating on taxes justifiable?",
    "Q181": "Is accepting a bribe justifiable?",
    "Q182": "Is homosexuality justifiable?",
    "Q183": "Is prostitution justifiable?",
    "Q184": "Is abortion justifiable?",
    "Q185": "Is divorce justifiable?",
    "Q186": "Is sex before marriage justifiable?",
    "Q187": "Is suicide justifiable?",
    "Q188": "Is euthanasia justifiable?",
    "Q189": "Is it justifiable for a man to beat his wife?",
    "Q190": "Is it justifiable for parents to beat their children?",
    "Q191": "Is violence against other people justifiable?",
    "Q192": "Is terrorism as a political, ideological or religious means justifiable?",
    "Q193": "Is casual sex justifiable?",
    "Q194": "Is political violence justifiable?",
    "Q195": "Is the death penalty justifiable?",
})

# --- State surveillance powers (1 = definitely should have the right) ------
_add({
    "Q196": "Should the government have the right to keep people under video surveillance in public areas?",
    "Q197": "Should the government have the right to monitor all emails and information exchanged on the internet?",
    "Q198": "Should the government have the right to collect information about anyone living in this country without their knowledge?",
})

# --- Politics and democracy -------------------------------------------------
_add({
    "Q199": "Are you interested in politics?",
    "Q200": "Do you follow politics in the news daily?",
    "Q201": "Do you get political information from daily newspapers?",
    "Q209": "Have you signed a petition?",
    "Q210": "Have you joined in a boycott?",
    "Q211": "Have you attended a peaceful demonstration?",
    "Q221": "Do you always vote in national elections?",
    "Q222": "Do you always vote in local elections?",
    "Q235": "Is having a strong leader who does not bother with parliament and elections a good way of governing this country?",
    "Q236": "Is having experts, not government, make decisions a good way of governing this country?",
    "Q237": "Is having the army rule a good way of governing this country?",
    "Q238": "Is having a democratic political system a good way of governing this country?",
    "Q239": "Is having a system governed by religious law, with no political parties or elections, a good way of governing this country?",
    "Q250": "Is it important to you to live in a country that is governed democratically?",
})
