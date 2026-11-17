"""Build the retail REIT Tableau storyboard (.twb) that reads the CSVs from 03_merge."""
import uuid
from xml.sax.saxutils import escape, quoteattr

DIR = "C:/ISA 401a/ISA-Section-A-Final-Project/data/processed"
Q, P = "federated.reitquarterly01", "federated.reitprofiles001"
TEAM = "Team [#]"

Q_COLS = [
    ("ticker", "string"), ("company", "string"), ("property_group", "string"), ("property_type", "string"),
    ("year", "integer"), ("quarter", "integer"), ("quarter_label", "string"), ("quarter_end", "date"),
    ("revenue_mm", "real"), ("net_income_mm", "real"), ("total_assets_mm", "real"),
    ("liabilities_to_assets", "real"), ("revenue_source", "string"), ("revenue_q4_derived", "string"),
    ("filing_date", "date"), ("accession", "string"), ("property_focus", "string"), ("occupancy_pct", "real"),
    ("same_property_noi_growth_pct", "real"), ("ffo_per_share", "real"), ("core_ffo_per_share", "real"),
    ("rent_spread_pct", "real"), ("guidance_change", "string"), ("net_debt_to_ebitda", "real"),
    ("llm_period_year", "integer"), ("llm_period_quarter", "integer"), ("llm_period_matches", "string"),
    ("quarter_end_trade_date", "date"), ("close_price", "real"), ("total_return_q_pct", "real"),
    ("treasury_10y_avg", "real"), ("treasury_10y_end", "real"), ("treasury_10y_change_bp", "real"),
    ("hq_city", "string"), ("hq_state", "string"), ("nareit_sector", "string"), ("price_on_nareit", "real"),
    ("nareit_as_of", "date"), ("exchange", "string"), ("hq_zip", "string"), ("return_1yr_pct", "real"),
    ("return_3yr_cagr_pct", "real"), ("return_5yr_cagr_pct", "real"), ("return_10yr_cagr_pct", "real"),
    ("dividend_yield_pct", "real"), ("trailing_dividend_ps", "real"), ("ffo_for_valuation", "real"),
    ("price_to_ffo", "real"), ("ffo_growth_yoy_pct", "real"),
]
P_COLS = [
    ("ticker", "string"), ("company", "string"), ("property_group", "string"), ("property_type", "string"),
    ("hq_city", "string"), ("hq_state", "string"), ("hq_zip", "string"), ("exchange", "string"),
    ("latest_quarter", "string"), ("occupancy_pct", "real"), ("same_property_noi_growth_pct", "real"),
    ("total_assets_mm", "real"), ("liabilities_to_assets", "real"), ("price_to_ffo", "real"),
    ("dividend_yield_pct", "real"), ("return_1yr_pct", "real"), ("return_3yr_cagr_pct", "real"),
    ("return_5yr_cagr_pct", "real"), ("treasury_10y_1yr_ago", "real"), ("excess_return_1yr_pct", "real"),
]
CAPTIONS = {
    "ticker": "Ticker", "company": "Company", "property_group": "Property Type", "quarter_end": "Quarter",
    "quarter_label": "Quarter Label", "occupancy_pct": "Occupancy (%)",
    "same_property_noi_growth_pct": "Same-Property NOI Growth (%)", "price_to_ffo": "Price / FFO",
    "total_return_q_pct": "Quarterly Total Return (%)", "treasury_10y_change_bp": "Change in 10-Yr Treasury (bp)",
    "treasury_10y_avg": "10-Yr Treasury (%)", "return_1yr_pct": "1-Year Total Return (%)",
    "liabilities_to_assets": "Liabilities / Assets", "hq_state": "HQ State", "hq_city": "HQ City",
    "dividend_yield_pct": "Dividend Yield (%)", "revenue_mm": "Revenue ($M)", "rent_spread_pct": "Rent Spread (%)",
    "net_debt_to_ebitda": "Net Debt / EBITDA",
    "treasury_10y_1yr_ago": "10-Yr Treasury Yield a Year Ago (%)", "excess_return_1yr_pct": "Return Above Treasury (pts)", "total_assets_mm": "Total Assets ($M)",
}
GROUP_COLORS = {"Shopping centers": "#4e79a7", "Malls & outlets": "#e15759", "Net lease": "#59a14f"}


def uid():
    return "{" + str(uuid.uuid4()).upper() + "}"


def role(dt, name):
    if dt in ("real",) or (dt == "integer" and name not in ("year", "quarter", "llm_period_year", "llm_period_quarter")):
        return "measure", "quantitative"
    if dt == "date":
        return "dimension", "ordinal"
    if dt == "integer":
        return "dimension", "ordinal"
    return "dimension", "nominal"


CALC = {
    "rate_move": ("10-Yr Treasury Move", "string", "dimension", "nominal",
                  'IF [treasury_10y_change_bp] > 25 THEN "Rates rose 25+ bp" '
                  'ELSEIF [treasury_10y_change_bp] < -25 THEN "Rates fell 25+ bp" '
                  'ELSE "Rates flat (within 25 bp)" END'),
    "reit_count": ("Number of REITs", "integer", "measure", "quantitative", "1"),
}
CALC_DS = {"rate_move": "q", "reit_count": "p"}


def calc_decl(name):
    cap, dt, rl, ty, f = CALC[name]
    return (f"<column caption={quoteattr(cap)} datatype='{dt}' name='[{name}]' role='{rl}' type='{ty}'>"
            f"<calculation class='tableau' formula={quoteattr(f)} /></column>")


def col_decl(name, dt):
    r, t = role(dt, name)
    cap = CAPTIONS.get(name)
    extra = ""
    if name == "hq_state":
        extra = " semantic-role='[State].[Name]'"
    if name == "hq_city":
        extra = " semantic-role='[City].[Name]'"
    cap_attr = f" caption={quoteattr(cap)}" if cap else ""
    return f"<column{cap_attr} datatype='{dt}' name='[{name}]' role='{r}' type='{t}'{extra} />"


def datasource(ds, caption, fname, cols, conn):
    table = fname.replace(".csv", "#csv")
    rel_cols = "\n".join(f"            <column datatype='{dt}' name='{n}' ordinal='{i}' />" for i, (n, dt) in enumerate(cols))
    rel = (f"<relation connection='{conn}' name='{fname}' table='[{table}]' type='table'>\n"
           f"          <columns character-set='UTF-8' header='yes' locale='en_US' separator=','>\n{rel_cols}\n"
           f"          </columns>\n        </relation>")
    obj_id = fname + "_" + uuid.uuid4().hex.upper()
    hyper = "Data/Extracts/" + fname.replace(".csv", ".hyper")
    rtype = {"string": 129, "integer": 20, "real": 5, "date": 133}
    agg = {"string": "Count", "integer": "Sum", "real": "Sum", "date": "Year"}
    mrecs = "\n".join(
        f"""            <metadata-record class='column'>
              <remote-name>{n}</remote-name>
              <remote-type>{rtype[dt]}</remote-type>
              <local-name>[{n}]</local-name>
              <parent-name>[Extract]</parent-name>
              <remote-alias>{n}</remote-alias>
              <ordinal>{i}</ordinal>
              <family>{fname}</family>
              <local-type>{dt}</local-type>
              <aggregation>{agg[dt]}</aggregation>
              <contains-null>true</contains-null>{"<collation flag='0' name='LEN_RUS' />" if dt == "string" else ""}
              <object-id>[{obj_id}]</object-id>
            </metadata-record>""" for i, (n, dt) in enumerate(cols))
    extract = f"""<extract count='-1' enabled='true' object-id='' units='records' user-specific='false'>
        <connection access_mode='readonly' author-locale='en_US' class='hyper' dbname='{hyper}' default-settings='hyper' schema='Extract' sslmode='' tablename='Extract' update-time='11/16/2026 08:30:00 PM' username='tableau_internal_user'>
          <relation name='Extract' table='[Extract].[Extract]' type='table' />
          <metadata-records>
{mrecs}
          </metadata-records>
        </connection>
      </extract>"""
    decls = "\n".join("      " + col_decl(n, dt) for n, dt in cols)
    which = "q" if fname.startswith("retail_reit_quarterly") else "p"
    decls += "\n" + "\n".join("      " + calc_decl(c) for c, w in CALC_DS.items() if w == which)
    style = ""
    if any(n == "property_group" for n, _ in cols):
        maps = "".join(f"<map to='{c}'><bucket>&quot;{escape(g)}&quot;</bucket></map>" for g, c in GROUP_COLORS.items())
        style = (f"<style><style-rule element='mark'><encoding attr='color' field='[none:property_group:nk]' type='palette'>"
                 f"{maps}</encoding></style-rule></style>")
    return f"""    <datasource caption={quoteattr(caption)} inline='true' name='{ds}' version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption={quoteattr(caption)} name='{conn}'>
            <connection class='textscan' directory={quoteattr(DIR)} filename='{fname}' password='' server='' />
          </named-connection>
        </named-connections>
        {rel}
      </connection>
      <aliases enabled='yes' />
      <column caption={quoteattr(fname)} datatype='table' name='[__tableau_internal_object_id__].[{obj_id}]' role='measure' type='quantitative' />
{decls}
      <column-instance column='[property_group]' derivation='None' name='[none:property_group:nk]' pivot='key' type='nominal' />
      {extract}
      <layout dim-ordering='alphabetic' measure-ordering='alphabetic' show-structure='true' />
      {style}
      <semantic-values>
        <semantic-value key='[Country].[Name]' value='&quot;United States&quot;' />
      </semantic-values>
      <object-graph>
        <objects>
          <object caption={quoteattr(fname)} id='{obj_id}'>
            <properties context=''>
              {rel}
            </properties>
            <properties context='extract'>
              <relation name='Extract' table='[Extract].[Extract]' type='table' />
            </properties>
          </object>
        </objects>
      </object-graph>
    </datasource>"""


# ---------- worksheet builder ----------
AGG = {"avg": "Avg", "sum": "Sum", "none": "None", "attr": "Attr"}


def inst(field, agg="none", kind=None, deriv=None, short=None):
    """Return (column-instance name, xml) for a field."""
    if kind is None:
        kind = "nk" if agg in ("none",) else "qk"
    short = short or agg
    tmap = {"nk": "nominal", "qk": "quantitative", "ok": "ordinal"}
    name = f"[{short}:{field}:{kind}]"
    d = deriv or AGG[agg]
    return name, f"<column-instance column='[{field}]' derivation='{d}' name='{name}' pivot='key' type='{tmap[kind]}' />"


def worksheet(name, ds, cols_by_name, title, subtitle, rows, cols, mark, color=None, label=None,
              detail=(), extra_insts=(), sort=None, group_filter=True, caption=None, axis_titles=None,
              tooltip_fields=(), axis_range=None, number_format=None, cull=True):
    """rows/cols: list of (field, agg, kind, deriv, short) tuples."""
    insts, deps = {}, set()
    def add(spec):
        n, x = inst(*spec)
        insts[n] = x
        deps.add(spec[0])
        return f"[{ds}].{n}"
    rows_s = " / ".join(add(r) for r in rows) if rows else ""
    cols_s = " / ".join(add(c) for c in cols) if cols else ""
    enc = []
    if color:
        enc.append(f"<color column='{add(color)}' />")
    if label:
        enc.append(f"<text column='{add(label)}' />")
    for d in detail:
        enc.append(f"<lod column='{add(d)}' />")
    for t in tooltip_fields:
        enc.append(f"<tooltip column='{add(t)}' />")
    for e in extra_insts:
        add(e)
    gf_ref = None
    if group_filter:
        gf_ref = add(("property_group", "none"))
    dep_cols = "\n".join("            " + col_decl(n, dt) for n, dt in cols_by_name if n in deps)
    dep_cols += "\n" + "\n".join("            " + calc_decl(c) for c in CALC if c in deps)
    dep_insts = "\n".join("            " + x for x in insts.values())
    filt = ""
    if group_filter:
        filt = (f"<filter class='categorical' column='{gf_ref}'>"
                f"<groupfilter function='level-members' level='[none:property_group:nk]' user:ui-enumeration='all' user:ui-marker='enumerate' />"
                f"</filter>")
    sorts = ""
    if sort:
        dim, meas, direction = sort
        sorts = (f"<shelf-sorts><shelf-sort-v2 dimension-to-sort='[{ds}].{inst(*dim)[0]}' direction='{direction}' "
                 f"is-on-innermost-dimension='true' measure-to-sort-by='[{ds}].{inst(*meas)[0]}' shelf='rows' /></shelf-sorts>")
    slices = f"<slices><column>{gf_ref}</column></slices>" if group_filter else ""
    label_style = ""
    if label:
        label_style = ("<style><style-rule element='mark'><format attr='mark-labels-show' value='true' />"
                       f"<format attr='mark-labels-cull' value='{'true' if cull else 'false'}' /></style-rule></style>")
    ax = ""
    if axis_titles:
        rules = "".join(f"<format attr='title' class='0' field='[{ds}].{inst(*spec)[0]}' scope='{scope}' value={quoteattr(txt)} />"
                        for spec, scope, txt in axis_titles)
        rng = ""
        if axis_range:
            spec, scope, lo, hi = axis_range
            rng = (f"<encoding attr='space' class='0' field='[{ds}].{inst(*spec)[0]}' field-type='quantitative' "
                   f"max='{hi}' min='{lo}' range-type='fixed' scope='{scope}' type='space' />")
        cell = ""
        if number_format:
            spec, fmt = number_format
            cell = (f"<style-rule element='cell'><format attr='text-format' field='[{ds}].{inst(*spec)[0]}' "
                    f"value={quoteattr(fmt)} /></style-rule>")
        ax = f"<style><style-rule element='axis'>{rng}{rules}</style-rule>{cell}</style>"
    else:
        ax = "<style />"
    sub = f"\n</run><run fontsize='10' fontcolor='#555555'>{escape(subtitle)}</run>" if subtitle else "</run>"
    xml = f"""    <worksheet name={quoteattr(name)}>
      <layout-options>
        <title>
          <formatted-text>
            <run bold='true' fontsize='14'>{escape(title)}{sub}
          </formatted-text>
        </title>
      </layout-options>
      <table>
        <view>
          <datasources>
            <datasource name='{ds}' />
          </datasources>
          <datasource-dependencies datasource='{ds}'>
{dep_cols}
{dep_insts}
          </datasource-dependencies>
          {filt}
          {sorts}
          {slices}
          <aggregation value='true' />
        </view>
        {ax}
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='{mark}' />
            <encodings>
              {''.join(enc)}
            </encodings>
            {label_style}
          </pane>
        </panes>
        <rows>{rows_s}</rows>
        <cols>{cols_s}</cols>
      </table>
      <simple-id uuid='{uid()}' />
    </worksheet>"""
    color_card = (f"<card pane-specification-id='0' param='{add(color)}' type='color' />" if color else "")
    filter_card = (f"<card mode='checkdropdown' param='{gf_ref}' type='filter' values='relevant' />" if group_filter else "")
    window = f"""    <window class='worksheet' name={quoteattr(name)}>
      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='2147483647'>
            <card type='columns' />
          </strip>
          <strip size='2147483647'>
            <card type='rows' />
          </strip>
          <strip size='31'>
            <card type='title' />
          </strip>
        </edge>
        <edge name='right'>
          <strip size='160'>
            {filter_card}
            {color_card}
          </strip>
        </edge>
      </cards>
      <simple-id uuid='{uid()}' />
    </window>"""
    return xml, window


WS, WIN = [], []
qd = dict(Q_COLS)


SHEET_DS = {}


def add_ws(*a, **k):
    SHEET_DS[a[0]] = a[1]
    x, w = worksheet(*a, **k)
    WS.append(x)
    WIN.append(w)


QUARTER = ("quarter_end", "none", "qk", "Quarter-Trunc", "tqr")
GROUP = ("property_group", "none")

add_ws("Occupancy Trend", Q, Q_COLS,
       "Net-lease REITs stay almost fully leased; shopping centers keep climbing",
       "Average occupancy by property type, quarterly, 2023-2026 (from earnings press releases)",
       rows=[("occupancy_pct", "avg")], cols=[QUARTER], mark="Line", color=GROUP,
       detail=(), axis_range=(("occupancy_pct", "avg"), "rows", 85, 100.5), axis_titles=[(("occupancy_pct", "avg"), "rows", "Average occupancy (%)"), (QUARTER, "cols", "Quarter")])

add_ws("NOI Growth Trend", Q, Q_COLS,
       "Shopping centers grew same-property NOI steadily; malls slowed in 2024-25",
       "Average year-over-year same-property NOI growth. Net-lease REITs are not shown: they do not report same-property NOI.",
       rows=[("same_property_noi_growth_pct", "avg")], cols=[QUARTER], mark="Line", color=GROUP,
       axis_titles=[(("same_property_noi_growth_pct", "avg"), "rows", "Same-property NOI growth (%)"), (QUARTER, "cols", "Quarter")])

add_ws("Valuation vs Growth", Q, Q_COLS,
       "Growth alone does not set the price: most REITs trade at 12-16x FFO, and malls are the cheapest",
       "Each dot is one REIT: typical (median) FFO-per-share growth vs. a year earlier, and average price / annualized FFO, 2024-2026",
       rows=[("price_to_ffo", "avg")], cols=[("ffo_growth_yoy_pct", "median", "qk", "Median", "med")], mark="Circle",
       color=GROUP, label=("ticker", "none"), detail=(("company", "none"),),
       axis_titles=[(("price_to_ffo", "avg"), "rows", "Price / FFO (x)"),
                    (("ffo_growth_yoy_pct", "median", "qk", "Median", "med"), "cols", "Median FFO per share growth, year over year (%)")])

add_ws("Returns vs Rates", Q, Q_COLS,
       "REIT returns drop when the 10-year Treasury rises, and net lease gets hit hardest",
       "Average quarterly stock total return by property type, grouped by how much the 10-year Treasury yield moved "
       "that quarter (2023-2026: 4 quarters fell 25+ bp, 6 were flat, 5 rose 25+ bp)",
       rows=[("total_return_q_pct", "avg")], cols=[("rate_move", "none"), GROUP], mark="Bar",
       color=GROUP, label=("total_return_q_pct", "avg"),
       number_format=(("total_return_q_pct", "avg"), "n#,##0.0;-#,##0.0"),
       axis_titles=[(("total_return_q_pct", "avg"), "rows", "Avg quarterly total return (%)")])

RET_SHEET = "1-Year Return vs Treasury"


def return_vs_treasury_sheet():
    ds, name = P, RET_SHEET
    R, T, X = "[sum:return_1yr_pct:qk]", "[sum:treasury_10y_1yr_ago:qk]", "[sum:excess_return_1yr_pct:qk]"
    TK, GP, CO = "[none:ticker:nk]", "[none:property_group:nk]", "[none:company:nk]"
    deps = "\n".join("            " + col_decl(n, dt) for n, dt in P_COLS
                     if n in ("ticker", "company", "property_group", "return_1yr_pct", "treasury_10y_1yr_ago",
                              "excess_return_1yr_pct"))
    insts = "".join([
        "<column-instance column='[ticker]' derivation='None' name='[none:ticker:nk]' pivot='key' type='nominal' />",
        "<column-instance column='[company]' derivation='None' name='[none:company:nk]' pivot='key' type='nominal' />",
        "<column-instance column='[property_group]' derivation='None' name='[none:property_group:nk]' pivot='key' type='nominal' />",
        "<column-instance column='[return_1yr_pct]' derivation='Sum' name='[sum:return_1yr_pct:qk]' pivot='key' type='quantitative' />",
        "<column-instance column='[treasury_10y_1yr_ago]' derivation='Sum' name='[sum:treasury_10y_1yr_ago:qk]' pivot='key' type='quantitative' />",
        "<column-instance column='[excess_return_1yr_pct]' derivation='Sum' name='[sum:excess_return_1yr_pct:qk]' pivot='key' type='quantitative' />",
    ])
    q = lambda n: f"[{ds}].{n}"
    fmt = "n#,##0.0;-#,##0.0"
    xml = f"""    <worksheet name={quoteattr(name)}>
      <layout-options>
        <title>
          <formatted-text>
            <run bold='true' fontsize='14'>20 of 24 retail REITs beat a 10-year Treasury last year, but net-lease REITs barely did
</run><run fontsize='10' fontcolor='#555555'>Bars: 1-year total return (as of Nov 13, 2026) with the 10-year Treasury yield from a year earlier inside (dark bar). Bottom line: return above the Treasury, in percentage points.</run>
          </formatted-text>
        </title>
      </layout-options>
      <table>
        <view>
          <datasources>
            <datasource name='{ds}' />
          </datasources>
          <datasource-dependencies datasource='{ds}'>
{deps}
            {insts}
          </datasource-dependencies>
          <filter class='categorical' column='{q(GP)}'><groupfilter function='level-members' level='{GP}' user:ui-enumeration='all' user:ui-marker='enumerate' /></filter>
          <shelf-sorts><shelf-sort-v2 dimension-to-sort='{q(TK)}' direction='DESC' is-on-innermost-dimension='true' measure-to-sort-by='{q(R)}' shelf='columns' /></shelf-sorts>
          <slices><column>{q(GP)}</column></slices>
          <aggregation value='true' />
        </view>
        <style>
          <style-rule element='axis'>
            <encoding attr='space' class='0' field='{q(T)}' field-type='quantitative' fold='true' scope='rows' synchronized='true' type='space' />
            <format attr='title' class='0' field='{q(R)}' scope='rows' value='1-year total return (%)' />
            <format attr='title' class='0' field='{q(X)}' scope='rows' value='Above Treasury (pts)' />
          </style-rule>
          <style-rule element='cell'>
            <format attr='text-format' field='{q(R)}' value='{fmt}' />
            <format attr='text-format' field='{q(X)}' value='{fmt}' />
          </style-rule>
        </style>
        <panes>
          <pane id='1' selection-relaxation-option='selection-relaxation-allow' y-axis-name='{q(R)}'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Bar' />
            <encodings>
              <color column='{q(GP)}' />
              <text column='{q(R)}' />
              <lod column='{q(CO)}' />
            </encodings>
            <style>
              <style-rule element='mark'>
                <format attr='mark-labels-show' value='true' />
                <format attr='size' value='1.4' />
              </style-rule>
            </style>
          </pane>
          <pane id='2' selection-relaxation-option='selection-relaxation-allow' y-axis-name='{q(T)}'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Bar' />
            <encodings>
              <lod column='{q(CO)}' />
            </encodings>
            <style>
              <style-rule element='mark'>
                <format attr='mark-color' value='#2b2b2b' />
                <format attr='size' value='0.35' />
              </style-rule>
            </style>
          </pane>
          <pane id='3' selection-relaxation-option='selection-relaxation-allow' y-axis-name='{q(X)}'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Line' />
            <style>
              <style-rule element='mark'>
                <format attr='mark-color' value='#000000' />
                <format attr='has-stroke' value='true' />
              </style-rule>
            </style>
          </pane>
        </panes>
        <rows>({q(R)} + {q(T)}) / {q(X)}</rows>
        <cols>{q(TK)}</cols>
      </table>
      <simple-id uuid='{uid()}' />
    </worksheet>"""
    win = f"""    <window class='worksheet' name={quoteattr(name)}>
      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='2147483647'>
            <card type='columns' />
          </strip>
          <strip size='2147483647'>
            <card type='rows' />
          </strip>
          <strip size='31'>
            <card type='title' />
          </strip>
        </edge>
        <edge name='right'>
          <strip size='160'>
            <card mode='checkdropdown' param='{q(GP)}' type='filter' values='relevant' />
            <card pane-specification-id='1' param='{q(GP)}' type='color' />
          </strip>
        </edge>
      </cards>
      <simple-id uuid='{uid()}' />
    </window>"""
    SHEET_DS[name] = ds
    WS.append(xml)
    WIN.append(win)


return_vs_treasury_sheet()

add_ws("Debt Load by REIT", P, P_COLS,
       "Malls carry the most debt",
       "Total liabilities as a share of total assets, latest quarter on file with the SEC",
       rows=[("ticker", "none")], cols=[("liabilities_to_assets", "sum")], mark="Bar", color=GROUP,
       detail=(("company", "none"),),
       sort=(("ticker", "none"), ("liabilities_to_assets", "sum"), "DESC"),
       axis_titles=[(("liabilities_to_assets", "sum"), "cols", "Liabilities / assets")])

x_, w_ = worksheet("REITs by Property Type", P, P_COLS,
                   "24 retail REITs, grouped by what they own",
                   "Each block is one REIT: 12 shopping center, 8 net lease, 4 mall/outlet",
                   rows=[GROUP], cols=[("reit_count", "sum")], mark="Bar", color=GROUP,
                   label=("ticker", "none"), detail=(("ticker", "none"),), group_filter=False, cull=False,
                   sort=(GROUP, ("reit_count", "sum"), "DESC"),
                   axis_titles=[(("reit_count", "sum"), "cols", "Number of REITs")])
WS.append(x_)
WIN.append(w_)

# ---------- text dashboards ----------
ZID = [100]


def nid():
    ZID[0] += 1
    return ZID[0]


def text_dashboard(name, runs, w=1100, h=760, side_sheet=None):
    body = "".join(runs)
    tw = 52000 if side_sheet else 90000
    side = (f"<zone h='84000' id='{nid()}' name={quoteattr(side_sheet)} type-v2='visual' w='44000' x='55000' y='8000' />"
            if side_sheet else "")
    vps = (f"<viewpoints><viewpoint name={quoteattr(side_sheet)}><zoom type='entire-view' /></viewpoint></viewpoints>"
           if side_sheet else "<viewpoints />")
    xml = f"""    <dashboard name={quoteattr(name)}>
      <style />
      <size maxheight='{h}' maxwidth='{w}' minheight='{h}' minwidth='{w}' sizing-mode='fixed' />
      <datasources />
      <zones>
        <zone h='100000' id='{nid()}' type-v2='layout-basic' w='100000' x='0' y='0'>
          <zone h='90000' id='{nid()}' type-v2='text' w='{tw}' x='3000' y='5000'>
            <formatted-text>{body}</formatted-text>
            <zone-style>
              <format attr='border-color' value='#000000' />
              <format attr='border-style' value='none' />
              <format attr='border-width' value='0' />
              <format attr='margin' value='12' />
            </zone-style>
          </zone>
          {side}
        </zone>
      </zones>
      <simple-id uuid='{uid()}' />
    </dashboard>"""
    win = f"""    <window class='dashboard' name={quoteattr(name)}>
      {vps}
      <active id='-1' />
      <simple-id uuid='{uid()}' />
    </window>"""
    return xml, win


def r(text, size=14, bold=False, color="#333333"):
    b = " bold='true'" if bold else ""
    return f"<run{b} fontcolor='{color}' fontsize='{size}'>{escape(text)}</run>"


NL = "<run>Æ&#10;</run>"
title_runs = [
    r("Retail REITs: Who Is Winning, and Does It Show Up in the Stock?", 22, True, "#1f3b57"), NL, NL,
    r("ISA 401 Final Project  |  Fall 2026  |  Section A  |  " + TEAM, 15, True), NL,
    r("Tyler Draeger  &  Kenneth Kelly", 15), NL, NL,
    r("The question", 16, True, "#1f3b57"), NL,
    r("Among the 24 publicly traded U.S. retail REITs, are shopping center owners doing better than malls and "
      "net-lease REITs on occupancy and rent growth, and does that show up in stock returns and valuations, "
      "or do interest rates matter more?", 13), NL, NL,
    r("Where the data comes from", 16, True, "#1f3b57"), NL,
    r("- Nareit REIT directory (web scraping): list of REITs, returns, dividends", 12), NL,
    r("- SEC EDGAR (API): revenue, net income, assets, liabilities", 12), NL,
    r("- 370 earnings press releases (LLM extraction): occupancy, NOI growth, FFO", 12), NL,
    r("- FRED (API): 10-year Treasury  |  Yahoo Finance (API): stock prices", 12), NL, NL,
    r("Use the Property Type filter on each page to focus on one group. Hover over any mark for details.", 12, False, "#666666"),
]
take_runs = [
    r("Takeaways", 24, True, "#1f3b57"), NL, NL,
    r("1.  Shopping centers have the strongest fundamentals: occupancy keeps rising and same-property NOI "
      "grows about 4% a year, faster than malls.", 14), NL, NL,
    r("2.  Malls are the cheapest and most indebted group, and the stocks bounced the most as investors "
      "came back to them.", 14), NL, NL,
    r("3.  Net-lease REITs are almost 100% leased but trade like bonds: a 1-point jump in the 10-year Treasury "
      "lined up with about a 16% drop in their quarterly return, vs. about 10% for shopping centers and malls.", 14), NL, NL,
    r("4.  Interest rates still drive a lot of the quarter-to-quarter stock moves for every group, so strong "
      "property results do not always show up in the stock right away.", 14), NL, NL,
    r("Limits: 2023-2026 only; FFO and occupancy come from company press releases (checked against the text); "
      "a few of the newest quarters are not in the SEC data yet.", 12, False, "#666666"),
]
DASH, DWIN = [], []
for nm, runs, side in (("Title", title_runs, "REITs by Property Type"), ("Takeaways", take_runs, None)):
    x, w = text_dashboard(nm, runs, side_sheet=side)
    DASH.append(x)
    DWIN.append(w)


def chart_dashboard(sheet, w=1100, h=760):
    ds = SHEET_DS[sheet]
    f = f"[{ds}].[none:property_group:nk]"
    dname = "Dash - " + sheet
    xml = f"""    <dashboard name={quoteattr(dname)}>
      <style />
      <size maxheight='{h}' maxwidth='{w}' minheight='{h}' minwidth='{w}' sizing-mode='fixed' />
      <datasources>
        <datasource name='{ds}' />
      </datasources>
      <datasource-dependencies datasource='{ds}'>
        <column caption='Property Type' datatype='string' name='[property_group]' role='dimension' type='nominal' />
        <column-instance column='[property_group]' derivation='None' name='[none:property_group:nk]' pivot='key' type='nominal' />
      </datasource-dependencies>
      <zones>
        <zone h='100000' id='{nid()}' type-v2='layout-basic' w='100000' x='0' y='0'>
          <zone h='98000' id='{nid()}' name={quoteattr(sheet)} type-v2='visual' w='82000' x='1000' y='1000' />
          <zone h='9000' id='{nid()}' mode='checkdropdown' name={quoteattr(sheet)} param='{f}' type-v2='filter' values='relevant' w='15500' x='83500' y='3000' />
          <zone h='24000' id='{nid()}' name={quoteattr(sheet)} pane-specification-id='0' param='{f}' type-v2='color' w='15500' x='83500' y='13000' />
        </zone>
      </zones>
      <simple-id uuid='{uid()}' />
    </dashboard>"""
    win = f"""    <window class='dashboard' name={quoteattr(dname)}>
      <viewpoints>
        <viewpoint name={quoteattr(sheet)}><zoom type='entire-view' /></viewpoint>
      </viewpoints>
      <active id='-1' />
      <simple-id uuid='{uid()}' />
    </window>"""
    return dname, xml, win


DASH_NAME = {}
for sh in SHEET_DS:
    dn, x, w = chart_dashboard(sh)
    DASH_NAME[sh] = dn
    DASH.append(x)
    DWIN.append(w)

# ---------- story ----------
points = [
    ("Title", "Retail REITs: the question"),
    ("Occupancy Trend", "Occupancy: net lease is full, centers are catching up"),
    ("NOI Growth Trend", "Growth: shopping centers lead"),
    ("Valuation vs Growth", "Growth vs. valuation"),
    ("Returns vs Rates", "Rates up, REITs down"),
    ("1-Year Return vs Treasury", "Last year: REITs vs. Treasuries"),
    ("Debt Load by REIT", "Who carries the most debt"),
    ("Takeaways", "Takeaways"),
]
SW, SH = 1100, 900
sp = "\n".join(f"                <story-point captured-sheet={quoteattr(DASH_NAME.get(s, s))} caption={quoteattr(c)} id='{i + 1}' />"
               for i, (s, c) in enumerate(points))
nav_id, flip_id = nid(), nid()
story = f"""    <dashboard name='Retail REIT Story' type='storyboard'>
      <style />
      <size maxheight='{SH}' maxwidth='{SW}' minheight='{SH}' minwidth='{SW}' sizing-mode='fixed' />
      <datasources />
      <zones>
        <zone h='100000' id='{nid()}' type-v2='layout-basic' w='100000' x='0' y='0'>
          <zone h='98340' id='{nid()}' param='vert' removable='false' type-v2='layout-flow' w='98426' x='787' y='830'>
            <zone h='3423' id='{nid()}' type-v2='title' w='98426' x='787' y='830' />
            <zone h='10477' id='{nav_id}' is-fixed='true' paired-zone-id='{flip_id}' removable='false' type-v2='flipboard-nav' w='98426' x='787' y='4253' />
            <zone h='84440' id='{flip_id}' paired-zone-id='{nav_id}' removable='false' type-v2='flipboard' w='98426' x='787' y='14730'>
              <flipboard active-id='1' nav-type='caption' show-nav-arrows='true'>
                <story-points>
{sp}
                </story-points>
              </flipboard>
            </zone>
          </zone>
        </zone>
      </zones>
      <simple-id uuid='{uid()}' />
    </dashboard>"""
story_win = f"""    <window class='dashboard' maximized='true' name='Retail REIT Story'>
      <viewpoints />
      <active id='-1' />
      <simple-id uuid='{uid()}' />
    </window>"""

wb = f"""<?xml version='1.0' encoding='utf-8' ?>

<!-- build 20262.26.0912.1023                               -->
<workbook original-version='18.1' source-build='2026.2.3 (20262.26.0912.1023)' source-platform='win' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest>
    <AnimationOnByDefault />
    <IntuitiveSorting />
    <IntuitiveSorting_SP2 />
    <MarkAnimation />
    <ObjectModelEncapsulateLegacy />
    <ObjectModelExtractV2 />
    <ObjectModelTableType />
    <SchemaViewerObjectModel />
    <SheetIdentifierTracking />
    <VConnDownstreamExtractsWithWarnings />
    <WindowsPersistSimpleIdentifiers />
  </document-format-change-manifest>
  <preferences>
    <preference name='ui.encoding.shelf.height' value='24' />
    <preference name='ui.shelf.height' value='26' />
  </preferences>
  <datasources>
{datasource(Q, "Retail REIT quarterly", "retail_reit_quarterly.csv", Q_COLS, "textscan.reitquarterly01")}
{datasource(P, "Retail REIT profiles", "retail_reit_profiles.csv", P_COLS, "textscan.reitprofiles001")}
  </datasources>
  <worksheets>
{chr(10).join(WS)}
  </worksheets>
  <dashboards>
{chr(10).join(DASH)}
{story}
  </dashboards>
  <windows source-height='30'>
{chr(10).join(WIN)}
{chr(10).join(DWIN)}
{story_win}
  </windows>
</workbook>
"""
import sys, csv, os, zipfile, datetime
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/twb/out"
CSV_DIR = sys.argv[2] if len(sys.argv) > 2 else DIR
os.makedirs(OUT + "/Data/Extracts", exist_ok=True)
open(OUT + "/retail_reit_story.twb", "w", encoding="utf-8").write(wb)

from tableauhyperapi import (HyperProcess, Telemetry, Connection, CreateMode, TableDefinition,
                             SqlType, TableName, Inserter, NULLABLE)
HT = {"string": SqlType.text(), "integer": SqlType.big_int(), "real": SqlType.double(), "date": SqlType.date()}


def conv(v, dt):
    if v in ("", "NA", "NaN"):
        return None
    if dt == "integer":
        return int(float(v))
    if dt == "real":
        return float(v)
    if dt == "date":
        return datetime.date.fromisoformat(v[:10])
    return v


with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp:
    for fname, cols in (("retail_reit_quarterly.csv", Q_COLS), ("retail_reit_profiles.csv", P_COLS)):
        path = OUT + "/Data/Extracts/" + fname.replace(".csv", ".hyper")
        rows = list(csv.DictReader(open(os.path.join(CSV_DIR, fname), encoding="utf-8")))
        missing = [n for n, _ in cols if n not in rows[0]]
        assert not missing, (fname, missing)
        with Connection(hp.endpoint, path, CreateMode.CREATE_AND_REPLACE) as con:
            con.catalog.create_schema("Extract")
            td = TableDefinition(TableName("Extract", "Extract"),
                                 [TableDefinition.Column(n, HT[dt], NULLABLE) for n, dt in cols])
            con.catalog.create_table(td)
            with Inserter(con, td) as ins:
                ins.add_rows([[conv(r[n], dt) for n, dt in cols] for r in rows])
                ins.execute()
        print(fname, len(rows), "rows")

with zipfile.ZipFile(OUT + "/retail_reit_story.twbx", "w", zipfile.ZIP_DEFLATED) as z:
    z.write(OUT + "/retail_reit_story.twb", "retail_reit_story.twb")
    for f in os.listdir(OUT + "/Data/Extracts"):
        z.write(OUT + "/Data/Extracts/" + f, "Data/Extracts/" + f)
print("ok")
