<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coverage Report</title>
    <style>
        *,*::before,*::after {{ box-sizing: border-box; }}

        :root {{
            --bg: #0f0f1a;
            --surface: #1a1a2e;
            --surface2: #16213e;
            --accent: #0f3460;
            --neon-blue: #00d4ff;
            --neon-green: #00ff88;
            --neon-red: #ff3860;
            --neon-yellow: #ffdd57;
            --neon-purple: #b388ff;
            --text: #e0e0e0;
            --text-dim: #8899aa;
            --glass: rgba(255,255,255,0.04);
            --glass-border: rgba(255,255,255,0.08);
        }}

        body {{
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            overflow-x: hidden;
        }}

        /* Animated background grid */
        body::before {{
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background:
                linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
            background-size: 60px 60px;
            animation: gridMove 20s linear infinite;
            pointer-events: none;
            z-index: 0;
        }}

        @keyframes gridMove {{
            0% {{ transform: translate(0, 0); }}
            100% {{ transform: translate(60px, 60px); }}
        }}

        /* Floating orbs */
        .orb {{
            position: fixed;
            border-radius: 50%;
            filter: blur(80px);
            opacity: 0.15;
            pointer-events: none;
            z-index: 0;
        }}
        .orb-1 {{ width: 400px; height: 400px; background: var(--neon-blue); top: -100px; right: -100px; animation: float1 15s ease-in-out infinite; }}
        .orb-2 {{ width: 350px; height: 350px; background: var(--neon-purple); bottom: -50px; left: -50px; animation: float2 18s ease-in-out infinite; }}
        .orb-3 {{ width: 250px; height: 250px; background: var(--neon-green); top: 50%; left: 50%; animation: float3 12s ease-in-out infinite; }}

        @keyframes float1 {{ 0%,100% {{ transform: translate(0,0); }} 50% {{ transform: translate(-60px, 80px); }} }}
        @keyframes float2 {{ 0%,100% {{ transform: translate(0,0); }} 50% {{ transform: translate(80px, -60px); }} }}
        @keyframes float3 {{ 0%,100% {{ transform: translate(-50%,-50%); }} 50% {{ transform: translate(-30%, -70%); }} }}

        .container {{
            max-width: 1280px;
            margin: 0 auto;
            padding: 30px 24px;
            position: relative;
            z-index: 1;
        }}

        /* Header */
        .header {{
            text-align: center;
            padding: 50px 30px 40px;
            margin-bottom: 30px;
            position: relative;
        }}
        .header h1 {{
            font-size: 2.4rem;
            font-weight: 700;
            margin: 0 0 8px;
            background: linear-gradient(135deg, var(--neon-blue), var(--neon-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.5px;
        }}
        .header .subtitle {{
            color: var(--text-dim);
            font-size: 0.95rem;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}

        /* Glass card */
        .card {{
            background: var(--glass);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 24px;
            position: relative;
            overflow: hidden;
            animation: cardIn 0.6s ease-out both;
        }}
        .card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(0,212,255,0.3), transparent);
        }}

        @keyframes cardIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .card:nth-child(2) {{ animation-delay: 0.1s; }}
        .card:nth-child(3) {{ animation-delay: 0.2s; }}
        .card:nth-child(4) {{ animation-delay: 0.3s; }}
        .card:nth-child(5) {{ animation-delay: 0.4s; }}
        .card:nth-child(6) {{ animation-delay: 0.5s; }}

        .card h2 {{
            font-size: 1.2rem;
            font-weight: 600;
            margin: 0 0 20px;
            color: var(--text);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .card h2 .icon {{ font-size: 1.3rem; }}

        /* Status banner */
        .status-banner {{
            text-align: center;
            padding: 24px;
            border-radius: 16px;
            margin-bottom: 24px;
            animation: cardIn 0.6s ease-out both;
            position: relative;
            overflow: hidden;
        }}
        .status-banner.pass {{
            background: linear-gradient(135deg, rgba(0,255,136,0.1), rgba(0,212,255,0.05));
            border: 1px solid rgba(0,255,136,0.2);
        }}
        .status-banner.fail {{
            background: linear-gradient(135deg, rgba(255,56,96,0.1), rgba(255,56,96,0.05));
            border: 1px solid rgba(255,56,96,0.2);
        }}
        .status-banner .status-icon {{
            font-size: 3rem;
            margin-bottom: 8px;
            animation: statusPulse 2s ease-in-out infinite;
        }}
        @keyframes statusPulse {{
            0%,100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
        }}
        .status-banner .status-text {{
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: 1px;
        }}
        .status-banner.pass .status-text {{ color: var(--neon-green); }}
        .status-banner.fail .status-text {{ color: var(--neon-red); }}

        /* Stat cards grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, var(--surface), var(--surface2));
            border: 1px solid var(--glass-border);
            border-radius: 14px;
            padding: 24px 20px;
            text-align: center;
            position: relative;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(0,212,255,0.15);
        }}
        .stat-card::after {{
            content: '';
            position: absolute;
            bottom: 0; left: 0; right: 0;
            height: 3px;
            border-radius: 0 0 14px 14px;
        }}
        .stat-card:nth-child(1)::after {{ background: linear-gradient(90deg, var(--neon-blue), var(--neon-purple)); }}
        .stat-card:nth-child(2)::after {{ background: linear-gradient(90deg, var(--neon-green), var(--neon-blue)); }}
        .stat-card:nth-child(3)::after {{ background: linear-gradient(90deg, var(--neon-purple), var(--neon-blue)); }}
        .stat-card:nth-child(4)::after {{ background: linear-gradient(90deg, var(--neon-yellow), var(--neon-green)); }}

        .stat-value {{
            font-size: 2.8rem;
            font-weight: 800;
            line-height: 1;
            margin-bottom: 6px;
        }}
        .stat-value.v-pass {{ color: var(--neon-green); text-shadow: 0 0 30px rgba(0,255,136,0.3); }}
        .stat-value.v-warn {{ color: var(--neon-yellow); text-shadow: 0 0 30px rgba(255,221,87,0.3); }}
        .stat-value.v-fail {{ color: var(--neon-red); text-shadow: 0 0 30px rgba(255,56,96,0.3); }}
        .stat-value.v-default {{ color: var(--neon-blue); text-shadow: 0 0 30px rgba(0,212,255,0.3); }}
        .stat-label {{ color: var(--text-dim); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; }}

        /* Gauge (coverage ring) */
        .gauge-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 40px;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }}
        .gauge {{
            position: relative;
            width: 180px;
            height: 180px;
        }}
        .gauge svg {{
            width: 180px;
            height: 180px;
            transform: rotate(-90deg);
        }}
        .gauge circle {{
            fill: none;
            stroke-width: 10;
            stroke-linecap: round;
        }}
        .gauge .track {{ stroke: rgba(255,255,255,0.06); }}
        .gauge .fill {{
            stroke-dasharray: 502;
            stroke-dashoffset: {gauge_offset};
            transition: stroke-dashoffset 1.5s ease-out;
            animation: gaugeAnim 1.5s ease-out;
        }}
        .gauge .fill.c-pass {{ stroke: url(#gradGreen); }}
        .gauge .fill.c-warn {{ stroke: url(#gradYellow); }}
        .gauge .fill.c-fail {{ stroke: url(#gradRed); }}
        @keyframes gaugeAnim {{
            from {{ stroke-dashoffset: 502; }}
        }}
        .gauge-label {{
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}
        .gauge-label .pct {{ font-size: 2.2rem; font-weight: 800; white-space: nowrap; }}
        .gauge-label .pct.c-pass {{ color: var(--neon-green); }}
        .gauge-label .pct.c-warn {{ color: var(--neon-yellow); }}
        .gauge-label .pct.c-fail {{ color: var(--neon-red); }}
        .gauge-label .sub {{ font-size: 0.8rem; color: var(--text-dim); }}

        .gauge-stats {{ text-align: left; }}
        .gauge-stats .gs-row {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0;
            border-bottom: 1px solid var(--glass-border);
            font-size: 0.95rem;
        }}
        .gs-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}

        /* Technique bar chart */
        .tech-bars {{ display: flex; flex-direction: column; gap: 14px; }}
        .tech-bar-row {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}
        .tech-bar-label {{ width: 140px; font-size: 0.85rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; text-align: right; flex-shrink: 0; }}
        .tech-bar-track {{ flex: 1; height: 28px; background: rgba(255,255,255,0.04); border-radius: 8px; overflow: hidden; position: relative; }}
        .tech-bar-fill {{
            height: 100%;
            border-radius: 8px;
            display: flex;
            align-items: center;
            padding-left: 12px;
            font-size: 0.8rem;
            font-weight: 700;
            color: white;
            animation: barGrow 1s ease-out both;
            position: relative;
            overflow: hidden;
        }}
        .tech-bar-fill::after {{
            content: '';
            position: absolute;
            top: 0; left: -100%; width: 50%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
            animation: shimmer 3s ease-in-out infinite;
        }}
        @keyframes shimmer {{
            0% {{ left: -100%; }}
            100% {{ left: 200%; }}
        }}
        @keyframes barGrow {{
            from {{ width: 0 !important; }}
        }}
        .tech-bar-fill.b-0 {{ background: linear-gradient(90deg, #00d4ff, #0099cc); }}
        .tech-bar-fill.b-1 {{ background: linear-gradient(90deg, #00ff88, #00cc6a); }}
        .tech-bar-fill.b-2 {{ background: linear-gradient(90deg, #b388ff, #7c4dff); }}
        .tech-bar-fill.b-3 {{ background: linear-gradient(90deg, #ffdd57, #ffab00); }}
        .tech-bar-fill.b-4 {{ background: linear-gradient(90deg, #ff3860, #cc2d4e); }}

        .tech-bar-row:nth-child(1) .tech-bar-fill {{ animation-delay: 0.1s; }}
        .tech-bar-row:nth-child(2) .tech-bar-fill {{ animation-delay: 0.2s; }}
        .tech-bar-row:nth-child(3) .tech-bar-fill {{ animation-delay: 0.3s; }}
        .tech-bar-row:nth-child(4) .tech-bar-fill {{ animation-delay: 0.4s; }}
        .tech-bar-row:nth-child(5) .tech-bar-fill {{ animation-delay: 0.5s; }}

        /* Table */
        .matrix-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 4px;
        }}
        .matrix-table thead th {{
            padding: 12px 16px;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-dim);
            border-bottom: 1px solid var(--glass-border);
            text-align: left;
            position: sticky;
            top: 0;
            background: var(--bg);
            z-index: 2;
        }}
        .matrix-table tbody tr {{
            background: var(--glass);
            transition: all 0.25s ease;
            animation: rowIn 0.4s ease-out both;
        }}
        .matrix-table tbody tr:hover {{
            background: rgba(0,212,255,0.06);
            transform: scale(1.005);
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }}
        .matrix-table tbody td {{
            padding: 14px 16px;
            font-size: 0.9rem;
            border-top: 1px solid transparent;
            border-bottom: 1px solid transparent;
        }}
        .matrix-table tbody tr td:first-child {{ border-radius: 10px 0 0 10px; border-left: 1px solid transparent; }}
        .matrix-table tbody tr td:last-child {{ border-radius: 0 10px 10px 0; border-right: 1px solid transparent; }}
        .matrix-table tbody tr:hover td {{ border-color: var(--glass-border); }}

        @keyframes rowIn {{
            from {{ opacity: 0; transform: translateX(-10px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}

        .matrix-table tbody tr:nth-child(1) {{ animation-delay: 0.05s; }}
        .matrix-table tbody tr:nth-child(2) {{ animation-delay: 0.10s; }}
        .matrix-table tbody tr:nth-child(3) {{ animation-delay: 0.15s; }}
        .matrix-table tbody tr:nth-child(4) {{ animation-delay: 0.20s; }}
        .matrix-table tbody tr:nth-child(5) {{ animation-delay: 0.25s; }}
        .matrix-table tbody tr:nth-child(6) {{ animation-delay: 0.30s; }}
        .matrix-table tbody tr:nth-child(7) {{ animation-delay: 0.35s; }}

        tr.uncovered {{ background: rgba(255,56,96,0.06) !important; }}
        tr.uncovered td:first-child {{ border-left: 3px solid var(--neon-red) !important; }}

        .req-id {{
            font-weight: 700;
            color: var(--neon-blue);
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 0.85rem;
        }}
        .tc-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }}
        .tc-chip {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            font-family: 'SF Mono', 'Fira Code', monospace;
            background: rgba(0,212,255,0.1);
            color: var(--neon-blue);
            border: 1px solid rgba(0,212,255,0.2);
            transition: all 0.2s;
        }}
        .tc-chip:hover {{
            background: rgba(0,212,255,0.2);
            box-shadow: 0 0 12px rgba(0,212,255,0.2);
        }}

        /* Check icons */
        .chk {{
            width: 26px; height: 26px;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            font-weight: 700;
        }}
        .chk-ok {{
            background: rgba(0,255,136,0.12);
            color: var(--neon-green);
            box-shadow: 0 0 10px rgba(0,255,136,0.1);
        }}
        .chk-miss {{
            background: rgba(255,56,96,0.08);
            color: rgba(255,56,96,0.5);
        }}

        /* Recommendations */
        .rec-card {{
            background: linear-gradient(135deg, rgba(255,221,87,0.05), rgba(255,171,0,0.03));
            border: 1px solid rgba(255,221,87,0.15);
        }}
        .rec-card ul {{ list-style: none; padding: 0; margin: 0; }}
        .rec-card li {{
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            display: flex;
            align-items: flex-start;
            gap: 10px;
            font-size: 0.9rem;
            color: var(--text-dim);
        }}
        .rec-card li:last-child {{ border-bottom: none; }}
        .rec-card li::before {{
            content: '!';
            background: rgba(255,221,87,0.15);
            color: var(--neon-yellow);
            width: 22px; height: 22px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.75rem;
            flex-shrink: 0;
            margin-top: 1px;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 30px 0 10px;
            color: var(--text-dim);
            font-size: 0.8rem;
            letter-spacing: 1px;
        }}
        .footer a {{ color: var(--neon-blue); text-decoration: none; }}

        /* Responsive */
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.6rem; }}
            .gauge-container {{ flex-direction: column; align-items: center; }}
            .tech-bar-label {{ width: 100px; font-size: 0.75rem; }}
            .stat-value {{ font-size: 2rem; }}
        }}
    </style>
</head>
<body>

<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>

<svg style="position:absolute;width:0;height:0;">
    <defs>
        <linearGradient id="gradGreen" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#00ff88"/>
            <stop offset="100%" style="stop-color:#00d4ff"/>
        </linearGradient>
        <linearGradient id="gradYellow" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#ffdd57"/>
            <stop offset="100%" style="stop-color:#ffab00"/>
        </linearGradient>
        <linearGradient id="gradRed" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#ff3860"/>
            <stop offset="100%" style="stop-color:#ff7043"/>
        </linearGradient>
    </defs>
</svg>

<div class="container">

    <div class="header">
        <h1>Coverage Report</h1>
        <div class="subtitle">{report_date} &middot; ISTQB Test Design</div>
    </div>

    <div class="status-banner {status_class}">
        <div class="status-icon">{status_icon}</div>
        <div class="status-text">{status_text}</div>
    </div>

    <div class="card" style="animation-delay:0.15s">
        <div class="gauge-container">
            <div class="gauge">
                <svg viewBox="0 0 180 180">
                    <circle class="track" cx="90" cy="90" r="80"/>
                    <circle class="fill {gauge_color_class}" cx="90" cy="90" r="80"/>
                </svg>
                <div class="gauge-label">
                    <div class="pct {gauge_color_class}">{coverage_pct}%</div>
                    <div class="sub">coverage</div>
                </div>
            </div>
            <div class="gauge-stats">
                <div class="gs-row"><span class="gs-dot" style="background:var(--neon-blue)"></span> <b>{total_req}</b>&nbsp; requirements</div>
                <div class="gs-row"><span class="gs-dot" style="background:var(--neon-green)"></span> <b>{covered_req}</b>&nbsp; covered</div>
                <div class="gs-row"><span class="gs-dot" style="background:var(--neon-red)"></span> <b>{uncovered_count}</b>&nbsp; uncovered</div>
                <div class="gs-row"><span class="gs-dot" style="background:var(--neon-purple)"></span> <b>{total_tc}</b>&nbsp; test cases</div>
            </div>
        </div>
    </div>

    {technique_html}

    <div class="card" style="animation-delay:0.35s">
        <h2><span class="icon">&#9638;</span> Traceability Matrix</h2>
        <table class="matrix-table">
            <thead>
                <tr>
                    <th>Requirement</th>
                    <th>Title</th>
                    <th>Test Cases</th>
                    <th style="text-align:center">+</th>
                    <th style="text-align:center">&minus;</th>
                    <th style="text-align:center">BVA</th>
                </tr>
            </thead>
            <tbody>
                {matrix_rows}
            </tbody>
        </table>
    </div>

    {recommendations_html}

    <div class="footer">
        ISTQB Coverage Report &middot; Generated by <a href="#">Manual Test Generator</a>
    </div>

</div>
</body>
</html>