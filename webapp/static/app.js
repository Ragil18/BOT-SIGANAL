/**
 * TradeSignal Pro - 60 FPS TradingView Canvas Engine & Real-time Controller
 */

class TradeSignalTerminal {
    constructor() {
        this.activeSymbol = 'BTC-USD';
        this.activeTimeframe = '1h';
        this.sensitivity = 0.3;
        this.activePreset = 'holy_trinity';
        this.activeModel = 'ml';
        this.predictionHorizon = 3;
        
        // Next-Gen Overlays & Price Lines
        this.showTpSl = true;
        this.showMlTarget = true;
        this.showRsi = false;
        this.showEma = false;
        this.showBb = false;
        this.tpPriceLine = null;
        this.slPriceLine = null;
        this.mlTargetPriceLine = null;
        this.cachedMlPrediction = null;
        this.ema20Series = null;
        this.ema50Series = null;
        this.ema200Series = null;
        this.bbUpperSeries = null;
        this.bbLowerSeries = null;

        // Paper Trading Simulator Engine & Terminal Dock
        this.paper = null;
        this.latestPrice = 0;
        
        this.chart = null;
        this.candlestickSeries = null;
        this.volumeSeries = null;
        
        this.isLoading = false;
        this.autoRefreshTimer = null;
        this.cachedCandles = [];
        
        // Backtest Studio Parameters
        this.btPreset = 'holy_trinity';
        this.btPeriod = '3mo';
        this.btInitialCapital = 100000;
        this.btSlPct = 3.0;
        this.btTpPct = 6.0;
        this.btCachedData = null;

        this.initDOM();
        this.paper = new PaperTradingEngine(this);
        this.autoPilot = new QuantAutoPilot(this, this.paper);
        this.wsManager = new BinanceWebSocketManager(this);
        this.initTradingViewChart();
        this.bindEvents();
        
        // Initial data bootstrap
        this.startISTClock();
        this.startBarCountdown();
        this.fetchTicker();
        this.loadMarketData();
        this.loadConfluence();
        this.wsManager.connect();
        
        // Auto-refresh poll every 10 seconds for real-time live price ticks
        this.autoRefreshTimer = setInterval(() => {
            this.loadMarketData(false);
            this.fetchTicker();
        }, 10000);
    }

    startISTClock() {
        const update = () => {
            const clockEl = document.getElementById('ist-clock');
            if (clockEl) {
                const now = new Date();
                clockEl.textContent = '🇮🇳 ' + now.toLocaleTimeString('en-IN', {
                    timeZone: 'Asia/Kolkata',
                    hour12: true,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                }) + ' IST';
            }
        };
        update();
        setInterval(update, 1000);
    }

    startBarCountdown() {
        const tfSecMap = {
            '1m': 60,
            '3m': 180,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        };

        const updateTimer = () => {
            const el = document.getElementById('countdown-timer');
            if (!el) return;
            const tfSec = tfSecMap[this.activeTimeframe] || 3600;
            const nowSec = Math.floor(Date.now() / 1000);
            const remSec = tfSec - (nowSec % tfSec);

            if (remSec >= 3600) {
                const h = Math.floor(remSec / 3600);
                const m = Math.floor((remSec % 3600) / 60);
                const s = remSec % 60;
                el.textContent = `⏳ ${h}h ${String(m).padStart(2, '0')}m`;
            } else {
                const m = Math.floor(remSec / 60);
                const s = remSec % 60;
                el.textContent = `⏳ ${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
            }
        };

        updateTimer();
        setInterval(updateTimer, 1000);
    }

    initDOM() {
        this.dom = {
            chartContainer: document.getElementById('tv-chart'),
            chartLoading: document.getElementById('chart-loading'),
            legendStats: document.getElementById('legend-stats'),
            displaySymbol: document.getElementById('display-symbol'),
            displayPrice: document.getElementById('display-price'),
            displayChange: document.getElementById('display-change'),
            timeframeBar: document.getElementById('timeframe-bar'),
            symbolChips: document.getElementById('symbol-chips'),
            customInput: document.getElementById('custom-symbol-input'),
            customBtn: document.getElementById('custom-symbol-btn'),
            sensitivitySlider: document.getElementById('sensitivity-slider'),
            sensitivityVal: document.getElementById('sensitivity-val'),
            btnRefresh: document.getElementById('btn-refresh'),
            tickerContainer: document.getElementById('ticker-container'),
            mtfPills: document.getElementById('mtf-pills'),
            mtfVerdictBadge: document.getElementById('mtf-verdict-badge'),
            mtfSummaryText: document.getElementById('mtf-summary-text'),
            signalBadge: document.getElementById('signal-action-badge'),
            signalScore: document.getElementById('signal-score-badge'),
            confidenceBar: document.getElementById('confidence-bar-fill'),
            signalRationale: document.getElementById('signal-rationale'),
            valTp: document.getElementById('val-tp'),
            valSl: document.getElementById('val-sl'),
            rrRatio: document.getElementById('rr-ratio'),
            thesisText: document.getElementById('thesis-text'),
            signalLogList: document.getElementById('signal-log-list'),
            presetChips: document.getElementById('preset-chips'),
            activePresetDesc: document.getElementById('active-preset-desc'),
            mlPredictionCard: document.getElementById('ml-prediction-card'),
            modelSwitch: document.getElementById('model-switch'),
            mlDirectionBadge: document.getElementById('ml-direction-badge'),
            mlExpectedReturn: document.getElementById('ml-expected-return'),
            probBull: document.getElementById('prob-bull'),
            probNeut: document.getElementById('prob-neut'),
            probBear: document.getElementById('prob-bear'),
            segBull: document.getElementById('seg-bull'),
            segNeut: document.getElementById('seg-neut'),
            segBear: document.getElementById('seg-bear'),
            mlEdgeTag: document.getElementById('ml-edge-tag'),
            mlAccTag: document.getElementById('ml-acc-tag'),
            mlModelTag: document.getElementById('ml-model-tag'),
            mlFactorsList: document.getElementById('ml-factors-list'),
            mlPredictedTarget: document.getElementById('ml-predicted-target'),
            btnRunInference: document.getElementById('btn-run-inference'),
            horizonChips: document.getElementById('horizon-chips'),
            aiPredictionPill: document.getElementById('ai-prediction-pill'),
            aiPillDot: document.querySelector('#ai-prediction-pill .ai-pill-dot'),
            aiPillText: document.getElementById('ai-pill-text'),
            aiPillBadge: document.getElementById('ai-pill-badge'),
            btnToggleTpSl: document.getElementById('btn-toggle-tpsl'),
            btnToggleMlTarget: document.getElementById('btn-toggle-ml-target'),
            btnToggleEma: document.getElementById('btn-toggle-ema'),
            btnToggleBb: document.getElementById('btn-toggle-bb'),
            btnOpenCmd: document.getElementById('btn-open-cmd'),
            cmdBackdrop: document.getElementById('cmd-palette-backdrop'),
            cmdInput: document.getElementById('cmd-palette-input'),
            cmdCloseEsc: document.getElementById('cmd-close-esc'),
            cmdResultsList: document.getElementById('cmd-results-list'),
            // Backtest Studio DOM Elements
            btPresetSelect: document.getElementById('bt-preset-select'),
            btPeriodChips: document.getElementById('bt-period-chips'),
            btInitialCapital: document.getElementById('bt-initial-capital'),
            btSlPct: document.getElementById('bt-sl-pct'),
            btTpPct: document.getElementById('bt-tp-pct'),
            btnRunBacktest: document.getElementById('btn-run-backtest'),
            btTotalReturn: document.getElementById('bt-total-return'),
            btAlphaSub: document.getElementById('bt-alpha-sub'),
            btSharpeVal: document.getElementById('bt-sharpe-val'),
            btSortinoSub: document.getElementById('bt-sortino-sub'),
            btWinrateVal: document.getElementById('bt-winrate-val'),
            btTradesSub: document.getElementById('bt-trades-sub'),
            btDrawdownVal: document.getElementById('bt-drawdown-val'),
            btCommissionSub: document.getElementById('bt-commission-sub'),
            btEquitySubtitle: document.getElementById('bt-equity-subtitle'),
            btTradesCount: document.getElementById('bt-trades-count'),
            btTradesTbody: document.getElementById('bt-trades-tbody'),
            equityCanvas: document.getElementById('equity-curve-canvas'),
            equityCanvasContainer: document.getElementById('equity-canvas-container'),
            // Market Regime Classifier DOM Elements
            marketRegimePill: document.getElementById('market-regime-pill'),
            regimeText: document.getElementById('regime-text'),
            apRegimeBanner: document.getElementById('ap-regime-banner'),
            apBannerText: document.getElementById('ap-banner-text'),
            // Modular Navigation & Workspace DOM Elements
            sidebarTabsNav: document.getElementById('sidebar-tabs-nav'),
            headerPresetSelect: document.getElementById('header-preset-select'),
            workspaceModes: document.getElementById('workspace-modes'),
            btnDockMinimize: document.getElementById('btn-dock-minimize'),
            btnDockExpand: document.getElementById('btn-dock-expand'),
            paperDock: document.getElementById('paper-terminal-dock'),
            // Advanced Tools & Countdown DOM Elements
            candleCountdown: document.getElementById('candle-countdown'),
            countdownTimer: document.getElementById('countdown-timer'),
            btnToggleRsi: document.getElementById('btn-toggle-rsi'),
            btnToggleSidebar: document.getElementById('btn-toggle-sidebar'),
            sidebarToggleGlyph: document.getElementById('sidebar-toggle-glyph'),
            dashboardLayout: document.getElementById('dashboard-layout'),
            intelSidebar: document.getElementById('intel-sidebar'),
            statFillBull: document.getElementById('stat-fill-bull'),
            statFillNeut: document.getElementById('stat-fill-neut'),
            statFillBear: document.getElementById('stat-fill-bear'),
            signalStrategyPill: document.getElementById('signal-strategy-pill'),
            consTrend: document.getElementById('cons-trend'),
            consMom: document.getElementById('cons-mom'),
            consVol: document.getElementById('cons-vol')
        };
    }

    initTradingViewChart() {
        if (!window.LightweightCharts) {
            console.error("TradingView LightweightCharts library not loaded");
            return;
        }

        const container = this.dom.chartContainer;
        this.chart = LightweightCharts.createChart(container, {
            layout: {
                background: { type: 'solid', color: '#0D121D' },
                textColor: '#8B98B2',
                fontFamily: "'JetBrains Mono', 'Inter', monospace",
                fontSize: 11
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.03)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.03)' }
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: {
                    color: 'rgba(0, 242, 254, 0.3)',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed
                },
                horzLine: {
                    color: 'rgba(0, 242, 254, 0.3)',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed
                }
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.08)',
                autoScale: true
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.08)',
                timeVisible: true,
                secondsVisible: false
            },
            localization: {
                locale: 'en-IN',
                dateFormat: 'yyyy-MM-dd',
                timeFormatter: timestamp => {
                    const d = new Date(timestamp * 1000);
                    return d.toLocaleTimeString('en-IN', {
                        timeZone: 'Asia/Kolkata',
                        hour12: true,
                        hour: '2-digit',
                        minute: '2-digit'
                    }) + ' IST';
                },
                dateFormatter: timestamp => {
                    const d = new Date(timestamp * 1000);
                    return d.toLocaleDateString('en-IN', {
                        timeZone: 'Asia/Kolkata',
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric'
                    });
                }
            }
        });

        // 1. Candlestick Series (Ultra-clean, crisp green and red)
        this.candlestickSeries = this.chart.addCandlestickSeries({
            upColor: '#00E676',
            downColor: '#FF3366',
            borderVisible: false,
            wickUpColor: '#00E676',
        });

        // 2. Overlay Line Series (EMA 20, 50, 200 & Bollinger Bands)
        this.ema20Series = this.chart.addLineSeries({
            color: '#00F2FE',
            lineWidth: 1.5,
            title: 'EMA 20',
            visible: this.showEma,
            crosshairMarkerVisible: false
        });

        this.ema50Series = this.chart.addLineSeries({
            color: '#FFB300',
            lineWidth: 1.5,
            title: 'EMA 50',
            visible: this.showEma,
            crosshairMarkerVisible: false
        });

        this.ema200Series = this.chart.addLineSeries({
            color: '#B388FF',
            lineWidth: 1.5,
            title: 'EMA 200',
            visible: this.showEma,
            crosshairMarkerVisible: false
        });

        this.bbUpperSeries = this.chart.addLineSeries({
            color: 'rgba(255, 179, 0, 0.6)',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dotted,
            title: 'BB Upper',
            visible: this.showBb,
            crosshairMarkerVisible: false
        });

        this.bbLowerSeries = this.chart.addLineSeries({
            color: 'rgba(255, 179, 0, 0.6)',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dotted,
            title: 'BB Lower',
            visible: this.showBb,
            crosshairMarkerVisible: false
        });

        // Crosshair move handler to update OHLC legend in IST
        this.chart.subscribeCrosshairMove(param => {
            if (!param || !param.time || !param.seriesData.get(this.candlestickSeries)) {
                return;
            }
            const data = param.seriesData.get(this.candlestickSeries);
            if (data) {
                const d = new Date(param.time * 1000);
                const timeStr = d.toLocaleTimeString('en-IN', {
                    timeZone: 'Asia/Kolkata',
                    hour12: true,
                    hour: '2-digit',
                    minute: '2-digit'
                }) + ' IST';
                const o = data.open.toLocaleString(undefined, { minimumFractionDigits: 2 });
                const h = data.high.toLocaleString(undefined, { minimumFractionDigits: 2 });
                const l = data.low.toLocaleString(undefined, { minimumFractionDigits: 2 });
                const c = data.close.toLocaleString(undefined, { minimumFractionDigits: 2 });
                this.dom.legendStats.textContent = `[${timeStr}]  O: ${o}  H: ${h}  L: ${l}  C: ${c}`;
            }
        });

        // Responsive resize
        const resizeObserver = new ResizeObserver(entries => {
            if (entries.length > 0 && this.chart) {
                const { width, height } = entries[0].contentRect;
                this.chart.applyOptions({ width, height });
            }
        });
        resizeObserver.observe(container);
    }

    resizeChart() {
        if (this.chart && this.dom.chartContainer) {
            this.chart.applyOptions({
                width: this.dom.chartContainer.clientWidth,
                height: this.dom.chartContainer.clientHeight
            });
        }
        if (this.btCachedData && this.btCachedData.equity_curve) {
            this.renderEquityCurveCanvas(this.btCachedData.equity_curve, this.btCachedData.initial_capital);
        }
    }

    copyDomPrice(price, side = null) {
        if (this.paper) {
            this.paper.setLimitPrice(price, side);
        }
    }

    setTimeframe(tf) {
        this.activeTimeframe = tf;
        this.dom.timeframeBar.querySelectorAll('.tf-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.tf === tf);
        });
    }

    bindEvents() {
        // 1-Click Indicator Strategy & Asset Combo Presets
        if (this.dom.presetChips) {
            this.dom.presetChips.addEventListener('click', (e) => {
                const chip = e.target.closest('.preset-chip');
                if (!chip) return;
                const preset = chip.dataset.preset;
                if (preset === this.activePreset) return;

                this.dom.presetChips.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                this.activePreset = preset;

                // Asset / strategy automatic timeframe recommendations
                if (preset === 'crypto_scalp' && (this.activeTimeframe === '1h' || this.activeTimeframe === '1d')) {
                    this.setTimeframe('5m');
                } else if (preset === 'stock_swing' && (this.activeTimeframe === '1m' || this.activeTimeframe === '3m' || this.activeTimeframe === '5m')) {
                    this.setTimeframe('1h');
                }

                const descMap = {
                    'holy_trinity': '👑 <b>Holy Trinity Active:</b> Trend (EMA 20/50) + Momentum (RSI 14) + Volatility (BB/ATR). Zero redundant noise.',
                    'crypto_scalp': '⚡ <b>Crypto Scalp Active:</b> Fast RSI (9) + Micro-Volatility Bands (1.8σ) + Rapid Volume Momentum.',
                    'stock_swing': '📈 <b>Stock Swing Active:</b> Macro Trend (EMA) + MACD Trend Following + Institutional Volume Conviction.',
                    'balanced': '⚙️ <b>Full Quant Active:</b> 10-indicator ensemble across all technical factors.'
                };
                if (this.dom.activePresetDesc) {
                    this.dom.activePresetDesc.innerHTML = descMap[preset] || '';
                }

                this.loadMarketData(true);
            });
        }

        // Quick Timeframe buttons
        this.dom.timeframeBar.addEventListener('click', (e) => {
            const btn = e.target.closest('.tf-btn');
            if (!btn) return;
            const tf = btn.dataset.tf;
            if (tf === this.activeTimeframe) return;

            this.setTimeframe(tf);
            this.loadMarketData(true);
        });

        // Symbol Chips
        this.dom.symbolChips.addEventListener('click', (e) => {
            const chip = e.target.closest('.chip');
            if (!chip) return;
            const sym = chip.dataset.symbol;
            if (sym === this.activeSymbol) return;

            this.dom.symbolChips.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            this.activeSymbol = sym;
            this.loadMarketData(true);
            this.loadConfluence();
        });

        // Custom Symbol input
        const submitCustomSymbol = () => {
            let sym = this.dom.customInput.value.trim().toUpperCase();
            if (!sym) return;
            if (!sym.includes('-') && !sym.includes('.')) {
                sym = `${sym}-USD`;
            }
            this.activeSymbol = sym;
            this.dom.symbolChips.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
            this.dom.customInput.value = '';
            this.loadMarketData(true);
            this.loadConfluence();
        };

        this.dom.customBtn.addEventListener('click', submitCustomSymbol);
        this.dom.customInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') submitCustomSymbol();
        });

        // Sensitivity slider
        this.dom.sensitivitySlider.addEventListener('input', (e) => {
            this.sensitivity = parseFloat(e.target.value);
            this.dom.sensitivityVal.textContent = this.sensitivity.toFixed(2);
        });

        this.dom.sensitivitySlider.addEventListener('change', () => {
            this.loadMarketData(false);
            this.loadConfluence();
        });

        // Manual refresh button
        this.dom.btnRefresh.addEventListener('click', () => {
            this.loadMarketData(true);
            this.loadConfluence();
            this.fetchTicker();
        });

        // AI / ML Model Toggle (Quant ML vs Deep LSTM)
        if (this.dom.modelSwitch) {
            this.dom.modelSwitch.addEventListener('click', (e) => {
                const btn = e.target.closest('.model-toggle-btn');
                if (!btn) return;
                const model = btn.dataset.model;
                if (model === this.activeModel) return;

                this.dom.modelSwitch.querySelectorAll('.model-toggle-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.activeModel = model;
                this.loadMarketData(false);
            });
        }

        // Forecast Horizon Selector (1, 3, 5, 10 Bars)
        if (this.dom.horizonChips) {
            this.dom.horizonChips.addEventListener('click', (e) => {
                const chip = e.target.closest('.horizon-chip');
                if (!chip) return;
                const h = parseInt(chip.dataset.horizon, 10);
                if (h === this.predictionHorizon) return;

                this.dom.horizonChips.querySelectorAll('.horizon-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                this.predictionHorizon = h;
                this.loadMarketData(false);
            });
        }

        // Header AI Prediction Pill Click -> Switch to Quant & AI Tab
        if (this.dom.aiPredictionPill) {
            this.dom.aiPredictionPill.addEventListener('click', () => {
                this.switchSidebarTab('quant');
                if (this.dom.mlPredictionCard) {
                    this.dom.mlPredictionCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    this.dom.mlPredictionCard.classList.add('flash-highlight');
                    setTimeout(() => this.dom.mlPredictionCard.classList.remove('flash-highlight'), 1200);
                }
            });
        }

        // Quick Model Inference Button
        if (this.dom.btnRunInference) {
            this.dom.btnRunInference.addEventListener('click', () => {
                this.runQuickInference();
            });
        }

        // Overlay Toggles (TP/SL, AI Target, EMA Ribbons, Bollinger Bands)
        if (this.dom.btnToggleTpSl) {
            this.dom.btnToggleTpSl.addEventListener('click', () => {
                this.showTpSl = !this.showTpSl;
                this.dom.btnToggleTpSl.classList.toggle('active', this.showTpSl);
                this.updateTpSlPriceLines(this.cachedTargets);
            });
        }

        if (this.dom.btnToggleMlTarget) {
            this.dom.btnToggleMlTarget.addEventListener('click', () => {
                this.showMlTarget = !this.showMlTarget;
                this.dom.btnToggleMlTarget.classList.toggle('active', this.showMlTarget);
                this.updateMlTargetPriceLine(this.cachedMlPrediction, this.latestPrice);
            });
        }

        if (this.dom.btnToggleEma) {
            this.dom.btnToggleEma.addEventListener('click', () => {
                this.showEma = !this.showEma;
                this.dom.btnToggleEma.classList.toggle('active', this.showEma);
                if (this.ema20Series) this.ema20Series.applyOptions({ visible: this.showEma });
                if (this.ema50Series) this.ema50Series.applyOptions({ visible: this.showEma });
                if (this.ema200Series) this.ema200Series.applyOptions({ visible: this.showEma });
                if (this.showEma && this.cachedCandles) this.updateOverlaySeries(this.cachedCandles);
            });
        }

        if (this.dom.btnToggleBb) {
            this.dom.btnToggleBb.addEventListener('click', () => {
                this.showBb = !this.showBb;
                this.dom.btnToggleBb.classList.toggle('active', this.showBb);
                if (this.bbUpperSeries) this.bbUpperSeries.applyOptions({ visible: this.showBb });
                if (this.bbLowerSeries) this.bbLowerSeries.applyOptions({ visible: this.showBb });
                if (this.showBb && this.cachedCandles) this.updateOverlaySeries(this.cachedCandles);
            });
        }

        if (this.dom.btnToggleRsi) {
            this.dom.btnToggleRsi.addEventListener('click', () => {
                this.showRsi = !this.showRsi;
                this.dom.btnToggleRsi.classList.toggle('active', this.showRsi);
                this.updateRsiIndicator(this.cachedCandles);
            });
        }

        if (this.dom.btnToggleSidebar) {
            this.dom.btnToggleSidebar.addEventListener('click', () => {
                this.toggleSidebar();
            });
        }

        // Paper Trading Simulator & Terminal Dock Event Bindings
        if (this.paper) {
            this.paper.bindEvents();
        }

        // Backtest Controls Event Bindings
        if (this.dom.btPresetSelect) {
            this.dom.btPresetSelect.addEventListener('change', (e) => {
                this.btPreset = e.target.value;
            });
        }
        if (this.dom.btPeriodChips) {
            this.dom.btPeriodChips.addEventListener('click', (e) => {
                const chip = e.target.closest('.bt-chip');
                if (!chip) return;
                this.dom.btPeriodChips.querySelectorAll('.bt-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                this.btPeriod = chip.dataset.period;
            });
        }
        if (this.dom.btInitialCapital) {
            this.dom.btInitialCapital.addEventListener('change', (e) => {
                this.btInitialCapital = parseFloat(e.target.value) || 100000;
            });
        }
        if (this.dom.btSlPct) {
            this.dom.btSlPct.addEventListener('change', (e) => {
                this.btSlPct = parseFloat(e.target.value) || 3.0;
            });
        }
        if (this.dom.btTpPct) {
            this.dom.btTpPct.addEventListener('change', (e) => {
                this.btTpPct = parseFloat(e.target.value) || 6.0;
            });
        }
        if (this.dom.btnRunBacktest) {
            this.dom.btnRunBacktest.addEventListener('click', () => {
                this.loadBacktestData(true);
            });
        }

        // Modular Navigation & Workspace Bindings
        this.bindSidebarTabs();
        this.bindDockControls();
        this.bindWorkspaceModes();
        this.bindHeaderPresets();

        // Command Palette Initialization (Ctrl+K or /)
        this.initCommandPalette();
    }

    bindSidebarTabs() {
        if (!this.dom.sidebarTabsNav) return;
        this.dom.sidebarTabsNav.addEventListener('click', (e) => {
            const btn = e.target.closest('.sb-tab');
            if (!btn) return;
            const tab = btn.dataset.sbTab;
            this.switchSidebarTab(tab);
        });
    }

    switchSidebarTab(tabName) {
        if (!this.dom.sidebarTabsNav) return;
        this.dom.sidebarTabsNav.querySelectorAll('.sb-tab').forEach(b => {
            b.classList.toggle('active', b.dataset.sbTab === tabName);
        });
        const panels = {
            'execute': document.getElementById('sb-panel-execute'),
            'quant': document.getElementById('sb-panel-quant'),
            'intel': document.getElementById('sb-panel-intel')
        };
        Object.entries(panels).forEach(([name, panel]) => {
            if (panel) {
                if (name === tabName) {
                    panel.style.display = 'flex';
                    panel.classList.add('active');
                } else {
                    panel.style.display = 'none';
                    panel.classList.remove('active');
                }
            }
        });
    }

    bindDockControls() {
        if (this.dom.btnDockMinimize) {
            this.dom.btnDockMinimize.addEventListener('click', () => {
                if (!this.dom.paperDock) return;
                const isMin = this.dom.paperDock.classList.toggle('minimized');
                if (isMin) this.dom.paperDock.classList.remove('expanded');
                this.handleResize();
            });
        }
        if (this.dom.btnDockExpand) {
            this.dom.btnDockExpand.addEventListener('click', () => {
                if (!this.dom.paperDock) return;
                const isExp = this.dom.paperDock.classList.toggle('expanded');
                if (isExp) this.dom.paperDock.classList.remove('minimized');
                this.handleResize();
            });
        }
    }

    bindWorkspaceModes() {
        if (!this.dom.workspaceModes) return;
        this.dom.workspaceModes.addEventListener('click', (e) => {
            const btn = e.target.closest('.mode-btn');
            if (!btn) return;
            const mode = btn.dataset.mode;
            this.setWorkspaceMode(mode);
        });
    }

    setWorkspaceMode(mode) {
        if (!this.dom.workspaceModes) return;
        this.dom.workspaceModes.querySelectorAll('.mode-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.mode === mode);
        });

        if (mode === 'terminal') {
            this.switchSidebarTab('execute');
            if (this.dom.paperDock) {
                this.dom.paperDock.classList.remove('expanded', 'minimized');
            }
        } else if (mode === 'quant') {
            this.switchSidebarTab('quant');
            if (this.dom.paperDock) {
                this.dom.paperDock.classList.remove('expanded');
            }
        } else if (mode === 'studio') {
            if (this.dom.paperDock) {
                this.dom.paperDock.classList.remove('minimized');
                this.dom.paperDock.classList.add('expanded');
            }
            if (this.paper) {
                this.paper.switchTab('backtest');
            }
            this.loadBacktestData(true);
        }
        this.handleResize();
    }

    bindHeaderPresets() {
        if (!this.dom.headerPresetSelect) return;
        this.dom.headerPresetSelect.addEventListener('change', (e) => {
            const preset = e.target.value;
            this.activePreset = preset;
            if (this.dom.presetChips) {
                this.dom.presetChips.querySelectorAll('.preset-chip').forEach(c => {
                    c.classList.toggle('active', c.dataset.preset === preset);
                });
            }
            if (this.dom.signalStrategyPill) {
                const labelMap = {
                    'holy_trinity': '👑 Holy Trinity',
                    'crypto_scalp': '⚡ Crypto Scalp',
                    'stock_swing': '📈 Stock Swing',
                    'balanced': '⚙️ All 10'
                };
                this.dom.signalStrategyPill.textContent = labelMap[preset] || preset;
            }
            this.loadMarketData(true);
        });
    }

    handleResize() {
        setTimeout(() => {
            this.resizeChart();
        }, 120);
    }

    toggleSidebar() {
        if (!this.dom.dashboardLayout) return;
        const isCollapsed = this.dom.dashboardLayout.classList.toggle('sidebar-collapsed');
        if (this.dom.sidebarToggleGlyph) {
            this.dom.sidebarToggleGlyph.textContent = isCollapsed ? '⇤' : '⇥';
        }
        if (this.dom.btnToggleSidebar) {
            this.dom.btnToggleSidebar.setAttribute('title', isCollapsed ? 'Expand Sidebar (Full Intel)' : 'Collapse Sidebar (Focus Chart)');
        }
        setTimeout(() => {
            this.resizeChart();
        }, 260);
    }

    calculateRSI(candles, period = 14) {
        if (!candles || candles.length <= period) return null;
        let gains = 0;
        let losses = 0;
        for (let i = 1; i <= period; i++) {
            const diff = candles[i].close - candles[i - 1].close;
            if (diff >= 0) gains += diff;
            else losses -= diff;
        }
        let avgGain = gains / period;
        let avgLoss = losses / period;

        for (let i = period + 1; i < candles.length; i++) {
            const diff = candles[i].close - candles[i - 1].close;
            if (diff >= 0) {
                avgGain = (avgGain * (period - 1) + diff) / period;
                avgLoss = (avgLoss * (period - 1)) / period;
            } else {
                avgGain = (avgGain * (period - 1)) / period;
                avgLoss = (avgLoss * (period - 1) - diff) / period;
            }
        }
        if (avgLoss === 0) return 100;
        const rs = avgGain / avgLoss;
        return 100 - (100 / (1 + rs));
    }

    updateRsiIndicator(candles) {
        if (!this.dom.btnToggleRsi) return;
        const rsiVal = this.calculateRSI(candles);
        if (rsiVal !== null) {
            const rounded = rsiVal.toFixed(1);
            let stateStyle = 'color: #94A3B8;';
            if (rsiVal >= 70) stateStyle = 'color: #FFB300; font-weight: 700;';
            else if (rsiVal <= 30) stateStyle = 'color: #00E676; font-weight: 700;';

            this.dom.btnToggleRsi.innerHTML = `<span class="btn-dot magenta"></span> <span style="${stateStyle}">RSI ${rounded}</span>`;
            if (this.showRsi) {
                this.dom.btnToggleRsi.classList.add('active');
            }
        }
    }

    async fetchTicker() {
        try {
            const res = await fetch('/api/ticker');
            if (!res.ok) return;
            const data = await res.json();
            
            let html = '';
            data.tickers.forEach(t => {
                const isPos = t.change_pct >= 0;
                const sign = isPos ? '+' : '';
                const chgClass = isPos ? 'pos' : 'neg';
                const formattedPrice = t.price > 10 ? t.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : t.price.toFixed(4);
                
                // Real-time micro SVG sparkline curve
                const sparkColor = isPos ? '#00E676' : '#FF3366';
                const sparkPoints = isPos 
                    ? '0,10 6,9 12,11 18,6 24,7 30,3 36,2' 
                    : '0,2 6,4 12,3 18,8 24,7 30,11 36,10';
                const sparkSvg = `<svg class="ticker-sparkline" width="36" height="12" viewBox="0 0 36 12" style="display:inline-block; vertical-align:middle; margin:0 4px;"><polyline fill="none" stroke="${sparkColor}" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" points="${sparkPoints}" /></svg>`;
                
                html += `
                    <div class="ticker-item" onclick="terminal.selectSymbol('${t.full_symbol}')">
                        <span class="ticker-sym">${t.symbol}</span>
                        ${sparkSvg}
                        <span class="ticker-price">$${formattedPrice}</span>
                        <span class="ticker-chg ${chgClass}">${sign}${t.change_pct}%</span>
                    </div>
                `;

                if (this.paper) {
                    this.paper.onPriceTick(t.full_symbol, t.price);
                }
            });
            this.dom.tickerContainer.innerHTML = html;
        } catch (err) {
            console.error("Ticker fetch error:", err);
        }
    }

    selectSymbol(symbol) {
        this.activeSymbol = symbol;
        this.dom.symbolChips.querySelectorAll('.chip').forEach(c => {
            c.classList.toggle('active', c.dataset.symbol === symbol);
        });
        if (this.wsManager) {
            this.wsManager.updateActiveSymbol(symbol);
        }
        this.loadMarketData(true);
        this.loadConfluence();
    }

    setTimeframe(tf) {
        this.activeTimeframe = tf;
        if (this.dom.timeframeBar) {
            this.dom.timeframeBar.querySelectorAll('.tf-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.tf === tf);
            });
        }
        if (this.wsManager) {
            this.wsManager.updateActiveTimeframe(tf);
        }
    }

    async loadMarketData(showLoader = true) {
        if (showLoader) {
            this.dom.chartLoading.classList.remove('hidden');
        }

        try {
            const url = `/api/candles?symbol=${encodeURIComponent(this.activeSymbol)}&timeframe=${this.activeTimeframe}&threshold=${this.sensitivity}&preset=${this.activePreset}&model_type=${this.activeModel}&horizon=${this.predictionHorizon}`;
            const res = await fetch(url);
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Failed to fetch candles');
            }

            const data = await res.json();
            
            // 1. Update 60 FPS Candlestick Series
            if (this.candlestickSeries && data.candles && data.candles.length > 0) {
                this.candlestickSeries.setData(data.candles);
                if (this.wsManager) {
                    this.wsManager.lastCandle = { ...data.candles[data.candles.length - 1] };
                }
                
                // 2. Set ONLY BUY/SELL markers at trigger transition points
                if (data.markers) {
                    this.candlestickSeries.setMarkers(data.markers);
                }
                
                if (showLoader) {
                    this.chart.timeScale().fitContent();
                }
            }

            // 3. Update Asset Price Header
            const cleanSym = this.activeSymbol.replace('-USD', '');
            this.dom.displaySymbol.textContent = `${cleanSym} · ${this.activeTimeframe.toUpperCase()}`;
            
            const curPrice = data.current_price;
            this.dom.displayPrice.textContent = `$${curPrice > 10 ? curPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : curPrice.toFixed(4)}`;

            // 4. Update Signal Decision Card
            const curSig = data.current_signal;
            const sigType = curSig.signal || 'HOLD';
            const strengthPct = Math.round(curSig.strength * 100);
            
            this.dom.signalBadge.textContent = sigType;
            this.dom.signalBadge.className = `signal-badge ${sigType.toLowerCase()}`;
            this.dom.signalScore.textContent = `${strengthPct}% Conf.`;
            this.dom.confidenceBar.style.width = `${strengthPct}%`;
            
            if (sigType === 'BUY') {
                this.dom.signalRationale.innerHTML = `🟢 <b>Bullish Expansion:</b> Edge factor score is <b>+${curSig.score}</b>, crossing upper threshold.`;
            } else if (sigType === 'SELL') {
                this.dom.signalRationale.innerHTML = `🔴 <b>Bearish Contraction:</b> Edge factor score is <b>${curSig.score}</b>, crossing lower trigger.`;
            } else {
                this.dom.signalRationale.innerHTML = `⚪ <b>Range-Bound / Neutral:</b> Score is <b>${curSig.score}</b> within sensitivity bounds (±${this.sensitivity}).`;
            }

            // 5. Update Risk Execution Targets
            if (data.targets) {
                const tp = data.targets.tp;
                const sl = data.targets.sl;
                this.dom.valTp.textContent = `$${tp > 10 ? tp.toLocaleString(undefined, { minimumFractionDigits: 2 }) : tp.toFixed(4)}`;
                this.dom.valSl.textContent = `$${sl > 10 ? sl.toLocaleString(undefined, { minimumFractionDigits: 2 }) : sl.toFixed(4)}`;
            }

            // 6. Update AI Quant Thesis
            if (data.thesis) {
                this.dom.thesisText.textContent = data.thesis;
            }

            // 7. Update Recent Triggered Signals Log
            if (data.markers && data.markers.length > 0) {
                const recent = [...data.markers].reverse().slice(0, 6);
                let logHtml = '';
                recent.forEach((m, idx) => {
                    const dateStr = new Date(m.time * 1000).toLocaleTimeString('en-IN', {
                        timeZone: 'Asia/Kolkata',
                        hour12: true,
                        hour: '2-digit',
                        minute: '2-digit'
                    }) + ' IST';
                    const isBuy = m.text.includes('BUY');
                    const badgeClass = isBuy ? 'buy' : 'sell';
                    const liveTag = idx === 0 ? '<span style="color:#00E676; font-size:10px; font-weight:700; margin-left:4px;">(Current)</span>' : '';
                    logHtml += `
                        <div class="log-item ${badgeClass}">
                            <span class="log-time">${dateStr} ${liveTag}</span>
                            <span class="log-badge ${badgeClass}">${m.text}</span>
                        </div>
                    `;
                });
                this.dom.signalLogList.innerHTML = logHtml;
            }

            // 8. Update AI / ML Predictive Engine Card
            if (data.ml_prediction) {
                this.renderMLPrediction(data.ml_prediction);
            }

            // 9. Cache data for real-time recalculations & overlays
            this.cachedCandles = data.candles || [];
            this.cachedTargets = data.targets;
            this.latestPrice = curPrice;

            // 10. Update On-Chart Visual TP/SL Price Lines
            this.updateTpSlPriceLines(data.targets);

            // 11. Update Overlay Series (EMA ribbons & Bollinger Bands)
            this.updateOverlaySeries(data.candles);

            // 12. Update Market Regime Classifier HUD & Guardrail Banners
            if (data.regime) {
                this.updateRegimeBadge(data.regime);
            }

            // Strategy Consensus Alignment Badges (Trend, Momentum, Volatility)
            if (this.dom.consTrend && curSig) {
                const isTrendBull = (curSig.score || 0) >= 0;
                this.dom.consTrend.textContent = `Trend: ${isTrendBull ? 'BULL' : 'BEAR'}`;
                this.dom.consTrend.className = `cons-pill ${isTrendBull ? 'on' : 'off'}`;
            }
            if (this.dom.consMom && curSig) {
                const isMomBull = (data.ml_prediction && data.ml_prediction.direction === 'BULLISH') || (curSig.score || 0) > 0.15;
                this.dom.consMom.textContent = `Mom: ${isMomBull ? 'BULL' : 'BEAR'}`;
                this.dom.consMom.className = `cons-pill ${isMomBull ? 'on' : 'off'}`;
            }
            if (this.dom.consVol) {
                const isNormalVol = !data.regime || !data.regime.includes('VOLATILE');
                this.dom.consVol.textContent = `Vol: ${isNormalVol ? 'NORMAL' : 'EXPANDING'}`;
                this.dom.consVol.className = `cons-pill ${isNormalVol ? 'on' : 'off'}`;
            }

            // Update RSI Indicator Badge
            if (data.candles && data.candles.length > 0) {
                this.updateRsiIndicator(data.candles);
            }

            // 13. Update Paper Trading Simulator & Terminal Dock with current market price tick
            if (this.paper) {
                this.paper.onPriceTick(this.activeSymbol, curPrice, data.candles);
            }

            // 14. Quant Auto-Pilot Autonomous Signal Evaluation with Macro Regime Guardrails & AI Filter
            if (this.autoPilot && data.current_signal) {
                this.autoPilot.evaluateSignal(this.activeSymbol, curPrice, data.current_signal, data.targets, data.regime, data.ml_prediction);
            }

            // 15. Real-Time Signal Transition Alerting & Chime
            const currentSig = data.current_signal ? data.current_signal.signal : null;
            if (currentSig && (currentSig === 'BUY' || currentSig === 'SELL') && this.lastSignal !== currentSig) {
                if (this.lastSignal !== null && this.paper) {
                    const icon = currentSig === 'BUY' ? '⚡' : '🔻';
                    const confPct = Math.round((data.current_signal.strength || 0.5) * 100);
                    const aiDir = data.ml_prediction ? ` | AI: ${data.ml_prediction.direction}` : '';
                    this.paper.showToast(currentSig === 'BUY' ? 'tp' : 'sl', `${icon} New Signal: ${this.activeSymbol.replace('-USD','')}`, `${currentSig} triggered with ${confPct}% conviction${aiDir}`);
                    if (this.wsManager && this.wsManager.audioEnabled) {
                        this.wsManager.playSuccessChime();
                    }
                }
                this.lastSignal = currentSig;
            }

        } catch (err) {
            console.error("Error loading market data:", err);
        } finally {
            this.dom.chartLoading.classList.add('hidden');
        }
    }

    updateRegimeBadge(regime) {
        if (!regime) return;
        this.cachedRegime = regime;

        const regType = regime.regime || 'CHOPPY_RANGE';
        let cls = 'chop';
        let badgeIcon = '🟡';

        if (regType === 'TRENDING_BULL') {
            cls = 'bull';
            badgeIcon = '🟢';
        } else if (regType === 'TRENDING_BEAR') {
            cls = 'bear';
            badgeIcon = '🔴';
        } else if (regType === 'VOLATILITY_HAZARD') {
            cls = 'hazard';
            badgeIcon = '⚡';
        }

        const adxVal = regime.metrics && regime.metrics.adx != null ? Number(regime.metrics.adx).toFixed(1) : null;
        const adxStr = adxVal ? ` · ADX ${adxVal}` : '';
        const pillText = `${regime.label.toUpperCase()}${adxStr}`;

        if (this.dom.marketRegimePill) {
            this.dom.marketRegimePill.className = `regime-pill ${cls}`;
            this.dom.marketRegimePill.title = `${regime.label}: ${regime.description}\nStrategy Bias: ${regime.strategy_bias}`;
        }
        if (this.dom.regimeText) {
            this.dom.regimeText.textContent = pillText;
        }

        if (this.dom.apRegimeBanner) {
            this.dom.apRegimeBanner.className = `ap-regime-banner ${cls}`;
        }
        if (this.dom.apBannerText) {
            let bannerMsg = '';
            if (regType === 'TRENDING_BULL') {
                bannerMsg = `Regime Guardrail: Longs Permitted · Counter-Trend Shorts Blocked (${adxStr.replace(' · ', '')})`;
            } else if (regType === 'TRENDING_BEAR') {
                bannerMsg = `Regime Guardrail: Shorts Permitted · Counter-Trend Longs Blocked (${adxStr.replace(' · ', '')})`;
            } else if (regType === 'VOLATILITY_HAZARD') {
                bannerMsg = `Regime Guardrail: Extreme Volatility Hazard · Auto-Pilot Disarmed for Capital Protection`;
            } else {
                bannerMsg = `Regime Guardrail: Mean-Reversion Mode · High Conviction Threshold ≥80% (${adxStr.replace(' · ', '')})`;
            }
            this.dom.apBannerText.textContent = bannerMsg;
        }
    }

    async loadNewsData() {
        const listEl = document.getElementById('news-articles-list');
        const badgeEl = document.getElementById('sentiment-gauge-badge');
        const markerEl = document.getElementById('sentiment-meter-marker');
        const scoreTextEl = document.getElementById('sentiment-score-text');
        const countTagEl = document.getElementById('headlines-count-tag');
        const mcapEl = document.getElementById('f-mcap');
        const f52wEl = document.getElementById('f-52w');
        const peEl = document.getElementById('f-pe');
        const targetEl = document.getElementById('f-target');

        if (!listEl) return;
        try {
            const res = await fetch(`/api/news?symbol=${encodeURIComponent(this.activeSymbol)}`);
            if (!res.ok) return;
            const data = await res.json();

            // 1. Sentiment Gauge
            const score = data.sentiment_score || 0.0;
            const pct = Math.max(0, Math.min(100, ((score + 1.0) / 2.0) * 100));
            if (markerEl) markerEl.style.left = `${pct}%`;

            const label = data.sentiment_label || 'NEUTRAL';
            const pillClass = label.includes('BULL') ? 'bullish' : (label.includes('BEAR') ? 'bearish' : 'neutral');
            if (badgeEl) {
                badgeEl.textContent = label;
                badgeEl.className = `sentiment-pill ${pillClass}`;
            }
            if (scoreTextEl) {
                const sign = score > 0 ? '+' : '';
                scoreTextEl.textContent = `Polarity Score: ${sign}${score.toFixed(2)} (${label})`;
            }

            // 2. Fundamentals
            const f = data.fundamentals || {};
            if (mcapEl) {
                const mcap = f.market_cap;
                if (mcap && mcap > 0) {
                    mcapEl.textContent = mcap >= 1e12 ? `$${(mcap/1e12).toFixed(2)}T` : (mcap >= 1e9 ? `$${(mcap/1e9).toFixed(2)}B` : `$${(mcap/1e6).toFixed(0)}M`);
                } else {
                    mcapEl.textContent = 'N/A';
                }
            }
            if (f52wEl) {
                const h = f.high_52w;
                const l = f.low_52w;
                f52wEl.textContent = (h && l) ? `$${l.toFixed(0)} - $${h.toFixed(0)}` : 'N/A';
            }
            if (peEl) {
                peEl.textContent = f.pe_trailing ? `${f.pe_trailing.toFixed(1)}x` : 'N/A';
            }
            if (targetEl) {
                targetEl.textContent = f.target_price ? `$${f.target_price.toFixed(2)}` : 'N/A';
            }

            // 3. Articles Feed
            const articles = data.headlines || [];
            if (countTagEl) countTagEl.textContent = `${articles.length} Headlines`;

            if (articles.length === 0) {
                listEl.innerHTML = '<div class="news-empty">No breaking headlines found for this asset in the last 24h.</div>';
                return;
            }

            let html = '';
            articles.forEach(a => {
                const badgeCls = (a.sentiment || 'NEUTRAL').toLowerCase();
                html += `
                    <a href="${a.link}" target="_blank" rel="noopener noreferrer" class="news-article-item">
                        <div class="article-content">
                            <span class="article-title">${a.title}</span>
                            <div class="article-meta">
                                <span class="article-source">${a.source}</span>
                                <span>·</span>
                                <span>${a.pub_date}</span>
                            </div>
                        </div>
                        <span class="article-badge ${badgeCls}">${a.sentiment}</span>
                    </a>
                `;
            });
            listEl.innerHTML = html;

        } catch (e) {
            console.error("Error loading news:", e);
        }
    }

    renderMLPrediction(pred) {
        if (!pred || !this.dom.mlPredictionCard) return;
        this.cachedMlPrediction = pred;

        const dir = (pred.direction || 'NEUTRAL').toUpperCase();
        if (this.dom.mlDirectionBadge) {
            this.dom.mlDirectionBadge.textContent = dir;
            this.dom.mlDirectionBadge.className = `ml-direction-badge ${dir.toLowerCase()}`;
        }

        if (this.dom.mlExpectedReturn) {
            const retSign = pred.expected_return_pct >= 0 ? '+' : '';
            this.dom.mlExpectedReturn.textContent = `${retSign}${pred.expected_return_pct}% (${pred.horizon_candles} Bars)`;
        }

        if (this.dom.mlPredictedTarget && this.latestPrice > 0) {
            const retPct = pred.expected_return_pct || 0;
            const targetPrice = this.latestPrice * (1 + (retPct / 100));
            const formattedTarget = targetPrice > 10 ? targetPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : targetPrice.toFixed(4);
            this.dom.mlPredictedTarget.textContent = `Target: $${formattedTarget}`;
        }

        const p = pred.probabilities || { bullish: 0.33, neutral: 0.34, bearish: 0.33 };
        const bPct = Math.round(p.bullish * 100);
        const nPct = Math.round(p.neutral * 100);
        const rPct = Math.round(p.bearish * 100);

        if (this.dom.probBull) this.dom.probBull.textContent = `${bPct}%`;
        if (this.dom.probNeut) this.dom.probNeut.textContent = `${nPct}%`;
        if (this.dom.probBear) this.dom.probBear.textContent = `${rPct}%`;

        if (this.dom.segBull) this.dom.segBull.style.width = `${bPct}%`;
        if (this.dom.segNeut) this.dom.segNeut.style.width = `${nPct}%`;
        if (this.dom.segBear) this.dom.segBear.style.width = `${rPct}%`;

        if (this.dom.statFillBull) this.dom.statFillBull.style.width = `${bPct}%`;
        if (this.dom.statFillNeut) this.dom.statFillNeut.style.width = `${nPct}%`;
        if (this.dom.statFillBear) this.dom.statFillBear.style.width = `${rPct}%`;

        if (this.dom.mlEdgeTag) {
            this.dom.mlEdgeTag.textContent = `Edge: ${pred.statistical_edge || '+0.0%'}`;
        }
        if (this.dom.mlAccTag) {
            const acc = pred.training_accuracy ? Math.round(pred.training_accuracy * 100) : 62;
            this.dom.mlAccTag.textContent = `Acc: ${acc}%`;
        }
        if (this.dom.mlModelTag) {
            this.dom.mlModelTag.textContent = pred.model_name || 'Active ML';
        }

        // Header Real-Time Telemetry Pill Sync
        if (this.dom.aiPredictionPill) {
            const confPct = Math.round((pred.confidence || 0.5) * 100);
            const pillClass = dir === 'BULLISH' ? 'bull' : (dir === 'BEARISH' ? 'bear' : 'neutral');
            this.dom.aiPredictionPill.className = `ai-prediction-pill ${pillClass}`;
            if (this.dom.aiPillText) {
                const sign = pred.expected_return_pct >= 0 ? '+' : '';
                this.dom.aiPillText.textContent = `AI: ${dir} (${sign}${pred.expected_return_pct}%)`;
            }
            if (this.dom.aiPillBadge) {
                this.dom.aiPillBadge.textContent = `${confPct}%`;
            }
        }

        if (this.dom.mlFactorsList && pred.top_drivers && pred.top_drivers.length > 0) {
            let driversHtml = '';
            pred.top_drivers.forEach(d => {
                const impactClass = (d.impact || 'neutral').toLowerCase();
                driversHtml += `
                    <div class="ml-factor-item">
                        <span class="factor-name">${d.factor}</span>
                        <span class="factor-impact ${impactClass}">${d.impact}</span>
                    </div>
                `;
            });
            this.dom.mlFactorsList.innerHTML = driversHtml;
        }

        // Update on-chart forward AI target line
        this.updateMlTargetPriceLine(pred, this.latestPrice);
    }

    updateMlTargetPriceLine(pred, curPrice) {
        if (!this.candlestickSeries) return;

        if (this.mlTargetPriceLine) {
            try { this.candlestickSeries.removePriceLine(this.mlTargetPriceLine); } catch (e) {}
            this.mlTargetPriceLine = null;
        }

        if (!this.showMlTarget || !pred || !curPrice || curPrice <= 0) return;

        const retPct = pred.expected_return_pct || 0;
        const targetPrice = curPrice * (1 + (retPct / 100));
        const sign = retPct >= 0 ? '+' : '';
        const dir = (pred.direction || 'NEUTRAL').toUpperCase();
        const color = dir === 'BULLISH' ? '#00E676' : (dir === 'BEARISH' ? '#FF3366' : '#00F2FE');
        const formattedTarget = targetPrice > 10 ? targetPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : targetPrice.toFixed(4);

        this.mlTargetPriceLine = this.candlestickSeries.createPriceLine({
            price: targetPrice,
            color: color,
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dotted,
            axisLabelVisible: true,
            title: `🧠 AI ${dir} (${pred.horizon_candles}B): $${formattedTarget} (${sign}${retPct}%)`
        });
    }

    async runQuickInference() {
        if (this.dom.btnRunInference) {
            this.dom.btnRunInference.classList.add('loading');
            this.dom.btnRunInference.textContent = '⏳ ...';
        }
        try {
            const url = `/api/predict?symbol=${encodeURIComponent(this.activeSymbol)}&timeframe=${this.activeTimeframe}&model_type=${this.activeModel}&horizon=${this.predictionHorizon}`;
            const res = await fetch(url);
            if (!res.ok) throw new Error('Inference error');
            const data = await res.json();
            this.renderMLPrediction(data);
            if (this.paper) {
                const confPct = Math.round((data.confidence || 0.5) * 100);
                this.paper.showToast('fill', '🧠 AI Inference Complete', `${data.model_name}: ${data.direction} (${confPct}% conviction)`);
            }
        } catch (err) {
            console.error('Quick inference failed:', err);
        } finally {
            if (this.dom.btnRunInference) {
                this.dom.btnRunInference.classList.remove('loading');
                this.dom.btnRunInference.textContent = '⚡ Infer';
            }
        }
    }

    async loadConfluence() {
        try {
            const url = `/api/confluence?symbol=${encodeURIComponent(this.activeSymbol)}&threshold=${this.sensitivity}`;
            const res = await fetch(url);
            if (!res.ok) return;
            const data = await res.json();

            // Update badge & summary
            this.dom.mtfVerdictBadge.textContent = data.verdict_badge;
            this.dom.mtfVerdictBadge.style.color = data.color;
            this.dom.mtfVerdictBadge.style.borderColor = data.color;
            this.dom.mtfSummaryText.textContent = `${data.verdict} (${data.buy_count}/${data.total_timeframes} Bullish Frames)`;

            // Update individual timeframe pills
            const matrixItems = data.matrix || data.timeframes || [];
            matrixItems.forEach(item => {
                const tfKey = (item.timeframe || item.tf || '').toLowerCase();
                const sig = (item.signal || item.status || 'HOLD').toUpperCase();
                const pill = this.dom.mtfPills.querySelector(`[data-tf="${tfKey}"]`);
                if (pill) {
                    pill.className = `mtf-pill ${sig.toLowerCase()}`;
                    const statusSpan = pill.querySelector('.pill-status');
                    if (statusSpan) {
                        statusSpan.textContent = sig;
                        if (sig === 'BUY') statusSpan.style.color = '#00E676';
                        else if (sig === 'SELL') statusSpan.style.color = '#FF3366';
                        else statusSpan.style.color = '#FFB300';
                    }
                }
            });
        } catch (err) {
            console.error("Error loading confluence:", err);
        }
    }

    // =========================================================================
    // On-Chart Price Lines & Technical Overlays
    // =========================================================================

    updateTpSlPriceLines(targets) {
        if (!this.candlestickSeries) return;

        // Clean up previous price lines
        if (this.tpPriceLine) {
            try { this.candlestickSeries.removePriceLine(this.tpPriceLine); } catch (e) {}
            this.tpPriceLine = null;
        }
        if (this.slPriceLine) {
            try { this.candlestickSeries.removePriceLine(this.slPriceLine); } catch (e) {}
            this.slPriceLine = null;
        }

        if (!this.showTpSl || !targets || !targets.tp || !targets.sl) return;

        this.tpPriceLine = this.candlestickSeries.createPriceLine({
            price: targets.tp,
            color: '#00E676',
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
            title: `🎯 TARGET TP $${targets.tp > 10 ? targets.tp.toLocaleString(undefined, {minimumFractionDigits: 2}) : targets.tp.toFixed(4)}`
        });

        this.slPriceLine = this.candlestickSeries.createPriceLine({
            price: targets.sl,
            color: '#FF3366',
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
            title: `🛡️ STOP LOSS $${targets.sl > 10 ? targets.sl.toLocaleString(undefined, {minimumFractionDigits: 2}) : targets.sl.toFixed(4)}`
        });
    }

    updateOverlaySeries(candles) {
        if (!candles || candles.length === 0) return;

        // Calculate & set EMA Ribbons (EMA 20, 50, 200)
        if (this.showEma) {
            if (this.ema20Series) this.ema20Series.setData(this.calculateEMA(candles, 20));
            if (this.ema50Series) this.ema50Series.setData(this.calculateEMA(candles, 50));
            if (this.ema200Series) this.ema200Series.setData(this.calculateEMA(candles, 200));
        }

        // Calculate & set Bollinger Bands
        if (this.showBb) {
            const { upper, lower } = this.calculateBB(candles, 20, 2.0);
            if (this.bbUpperSeries) this.bbUpperSeries.setData(upper);
            if (this.bbLowerSeries) this.bbLowerSeries.setData(lower);
        }
    }

    calculateEMA(candles, period) {
        if (!candles || candles.length < period) return [];
        const k = 2 / (period + 1);
        const res = [];
        let ema = candles[0].close;
        for (let i = 0; i < candles.length; i++) {
            ema = i === 0 ? candles[i].close : (candles[i].close * k) + (ema * (1 - k));
            if (i >= period - 1) {
                res.push({ time: candles[i].time, value: parseFloat(ema.toFixed(4)) });
            }
        }
        return res;
    }

    calculateBB(candles, period = 20, numStd = 2.0) {
        if (!candles || candles.length < period) return { upper: [], lower: [] };
        const upper = [];
        const lower = [];
        for (let i = period - 1; i < candles.length; i++) {
            const slice = candles.slice(i - period + 1, i + 1).map(c => c.close);
            const mean = slice.reduce((a, b) => a + b, 0) / period;
            const variance = slice.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / period;
            const std = Math.sqrt(variance);
            upper.push({ time: candles[i].time, value: parseFloat((mean + (numStd * std)).toFixed(4)) });
            lower.push({ time: candles[i].time, value: parseFloat((mean - (numStd * std)).toFixed(4)) });
        }
        return { upper, lower };
    }

    async loadNewsData() {
        const gaugeBadge = document.getElementById('sentiment-gauge-badge');
        const meterFill = document.getElementById('sentiment-meter-fill');
        const meterMarker = document.getElementById('sentiment-meter-marker');
        const scoreText = document.getElementById('sentiment-score-text');
        const headlinesList = document.getElementById('news-articles-list');
        const headlinesCount = document.getElementById('headlines-count-tag');
        
        try {
            const res = await fetch(`/api/news?symbol=${encodeURIComponent(this.activeSymbol)}`);
            if (!res.ok) return;
            const data = await res.json();
            
            const score = data.sentiment_score || 0.0;
            const pct = Math.max(0, Math.min(100, Math.round(((score + 1.0) / 2.0) * 100)));
            
            if (meterFill) meterFill.style.width = `${pct}%`;
            if (meterMarker) meterMarker.style.left = `${pct}%`;
            if (scoreText) scoreText.textContent = `Polarity Score: ${score > 0 ? '+' : ''}${score.toFixed(3)}`;
            
            if (gaugeBadge) {
                gaugeBadge.textContent = data.sentiment_label || 'NEUTRAL';
                const label = (data.sentiment_label || '').toLowerCase();
                if (label.includes('greed') || label.includes('bullish')) {
                    gaugeBadge.className = 'sentiment-pill pos';
                } else if (label.includes('fear') || label.includes('bearish')) {
                    gaugeBadge.className = 'sentiment-pill neg';
                } else {
                    gaugeBadge.className = 'sentiment-pill neutral';
                }
            }
            
            // Fundamentals
            const f = data.fundamentals || {};
            const setF = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val || '--';
            };
            setF('f-mcap', f.market_cap ? (typeof f.market_cap === 'number' ? `$${(f.market_cap / 1e9).toFixed(2)}B` : f.market_cap) : '--');
            setF('f-52w', f['52w_high'] && f['52w_low'] ? `$${f['52w_low']} - $${f['52w_high']}` : '--');
            setF('f-pe', f.pe_ratio ? f.pe_ratio.toFixed(2) : '--');
            setF('f-target', f.target_price ? `$${f.target_price}` : '--');
            
            // Headlines
            if (headlinesCount) headlinesCount.textContent = `${data.headline_count || 0} Articles`;
            if (headlinesList && data.headlines) {
                if (data.headlines.length === 0) {
                    headlinesList.innerHTML = `<div class="news-empty">No recent news catalysts found for ${this.activeSymbol}.</div>`;
                } else {
                    headlinesList.innerHTML = data.headlines.map(h => {
                        const hScore = h.score || 0;
                        const scorePillClass = hScore > 0.05 ? 'pos' : (hScore < -0.05 ? 'neg' : 'neutral');
                        const sign = hScore > 0 ? '+' : '';
                        const dateFormatted = h.published ? new Date(h.published).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';
                        return `
                            <div class="news-article-item">
                                <div class="article-top-row">
                                    <span class="article-source">${h.source || 'News'}</span>
                                    <span class="article-score-badge ${scorePillClass}">${sign}${hScore.toFixed(2)}</span>
                                </div>
                                <a href="${h.link}" target="_blank" rel="noopener noreferrer" class="article-headline">${h.title}</a>
                                ${dateFormatted ? `<div class="article-date">${dateFormatted}</div>` : ''}
                            </div>
                        `;
                    }).join('');
                }
            }
        } catch (e) {
            console.error("News fetch error:", e);
        }
    }

    async loadBacktestData(force = false) {
        if (!force && this.btCachedData && this.btCachedData.symbol === this.activeSymbol && this.btCachedData.preset === this.btPreset) {
            this.renderBacktestResults(this.btCachedData);
            return;
        }

        if (this.dom.btnRunBacktest) {
            this.dom.btnRunBacktest.innerHTML = `<span class="spinner" style="width:14px; height:14px; border-width:2px;"></span> Simulating...`;
            this.dom.btnRunBacktest.disabled = true;
        }

        try {
            const slFrac = (this.btSlPct || 3.0) / 100.0;
            const tpFrac = (this.btTpPct || 6.0) / 100.0;
            const url = `/api/backtest?symbol=${encodeURIComponent(this.activeSymbol)}&timeframe=${encodeURIComponent(this.activeTimeframe)}&period=${encodeURIComponent(this.btPeriod)}&threshold=${this.sensitivity}&preset=${encodeURIComponent(this.btPreset)}&initial_capital=${this.btInitialCapital}&stop_loss_pct=${slFrac}&take_profit_pct=${tpFrac}`;
            
            const res = await fetch(url);
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Backtest failed');
            }

            const data = await res.json();
            this.btCachedData = data;
            this.renderBacktestResults(data);

            if (this.paper) {
                this.paper.showToast('fill', 'Backtest Complete', `Return: ${data.total_return >= 0 ? '+' : ''}${data.total_return}% (${data.total_trades} Trades)`);
            }
        } catch (err) {
            console.error("Backtest error:", err);
            if (this.paper) {
                this.paper.showToast('sl', 'Backtest Error', err.message);
            }
        } finally {
            if (this.dom.btnRunBacktest) {
                this.dom.btnRunBacktest.innerHTML = `<span class="btn-icon">🚀</span> Run Simulation`;
                this.dom.btnRunBacktest.disabled = false;
            }
        }
    }

    renderBacktestResults(data) {
        const sign = data.total_return >= 0 ? '+' : '';
        const retClass = data.total_return > 0 ? 'pos' : (data.total_return < 0 ? 'neg' : '');

        if (this.dom.btTotalReturn) {
            this.dom.btTotalReturn.textContent = `${sign}${data.total_return}%`;
            this.dom.btTotalReturn.className = `bt-kpi-val ${retClass}`;
        }
        if (this.dom.btAlphaSub) {
            const alphaSign = data.alpha >= 0 ? '+' : '';
            this.dom.btAlphaSub.textContent = `Alpha: ${alphaSign}${data.alpha}% (vs B&H: ${data.buy_hold_return}%)`;
        }

        if (this.dom.btSharpeVal) {
            this.dom.btSharpeVal.textContent = data.sharpe_ratio.toFixed(2);
            this.dom.btSharpeVal.className = `bt-kpi-val ${data.sharpe_ratio >= 1.0 ? 'pos' : (data.sharpe_ratio < 0 ? 'neg' : '')}`;
        }
        if (this.dom.btSortinoSub) {
            this.dom.btSortinoSub.textContent = `Sortino: ${data.sortino_ratio.toFixed(2)} | Calmar: ${data.calmar_ratio.toFixed(2)}`;
        }

        if (this.dom.btWinrateVal) {
            this.dom.btWinrateVal.textContent = `${data.win_rate}% (PF: ${data.profit_factor})`;
            this.dom.btWinrateVal.className = `bt-kpi-val ${data.win_rate >= 50 ? 'pos' : 'neg'}`;
        }
        if (this.dom.btTradesSub) {
            this.dom.btTradesSub.textContent = `${data.total_trades} Trades (${data.profitable_trades} Wins / ${data.losing_trades} Losses)`;
        }

        if (this.dom.btDrawdownVal) {
            this.dom.btDrawdownVal.textContent = `${data.max_drawdown}%`;
            this.dom.btDrawdownVal.className = `bt-kpi-val ${Math.abs(data.max_drawdown) > 15 ? 'neg' : ''}`;
        }
        if (this.dom.btCommissionSub) {
            this.dom.btCommissionSub.textContent = `Total Comm: $${data.total_commission.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        }

        if (this.dom.btEquitySubtitle) {
            const finalFormatted = data.final_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
            const initFormatted = data.initial_capital.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
            this.dom.btEquitySubtitle.textContent = `$${initFormatted} → $${finalFormatted}`;
        }

        if (this.dom.btTradesCount) {
            this.dom.btTradesCount.textContent = `${data.total_trades} Trades`;
        }

        // Render trades table
        if (this.dom.btTradesTbody) {
            if (!data.trades || data.trades.length === 0) {
                this.dom.btTradesTbody.innerHTML = `<tr><td colspan="4" class="table-empty-row">No trades executed with current sensitivity and risk settings.</td></tr>`;
            } else {
                this.dom.btTradesTbody.innerHTML = [...data.trades].reverse().map(t => {
                    const isWin = (t.profit_loss || 0) >= 0;
                    const pnlClass = isWin ? 'pos' : 'neg';
                    const tSign = isWin ? '+' : '';
                    return `
                        <tr>
                            <td><span class="side-badge ${t.type.toLowerCase().includes('buy') ? 'buy' : 'sell'}">${t.type}</span></td>
                            <td>$${t.price > 10 ? t.price.toLocaleString(undefined, {minimumFractionDigits: 2}) : t.price.toFixed(4)}</td>
                            <td class="${pnlClass}">${tSign}$${t.profit_loss.toFixed(2)}</td>
                            <td class="${pnlClass}">${tSign}${t.profit_loss_pct.toFixed(2)}%</td>
                        </tr>
                    `;
                }).join('');
            }
        }

        // Render interactive Canvas Equity Curve
        this.renderEquityCurveCanvas(data.equity_curve, data.initial_capital);
    }

    renderEquityCurveCanvas(equityCurve, initialCapital) {
        const canvas = this.dom.equityCanvas;
        const container = this.dom.equityCanvasContainer;
        if (!canvas || !container || !equityCurve || equityCurve.length === 0) return;

        const dpr = window.devicePixelRatio || 1;
        const rect = container.getBoundingClientRect();
        const width = rect.width || 400;
        const height = rect.height || 220;

        canvas.width = width * dpr;
        canvas.height = height * dpr;

        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
        ctx.clearRect(0, 0, width, height);

        const values = equityCurve.map(pt => pt.value);
        const minVal = Math.min(...values, initialCapital * 0.98);
        const maxVal = Math.max(...values, initialCapital * 1.02);
        const range = (maxVal - minVal) || 1;

        const padX = 20;
        const padY = 24;
        const drawW = width - (padX * 2);
        const drawH = height - (padY * 2);

        const getX = (idx) => padX + (idx / Math.max(1, equityCurve.length - 1)) * drawW;
        const getY = (val) => padY + drawH - ((val - minVal) / range) * drawH;

        // Baseline (Initial capital dashed reference line)
        const baseY = getY(initialCapital);
        ctx.save();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
        ctx.setLineDash([4, 4]);
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padX, baseY);
        ctx.lineTo(padX + drawW, baseY);
        ctx.stroke();

        ctx.fillStyle = '#8B98B2';
        ctx.font = '10px JetBrains Mono, monospace';
        ctx.fillText(`Baseline: $${initialCapital.toLocaleString()}`, padX + 6, baseY - 6);
        ctx.restore();

        // Area Gradient fill under equity curve
        const isNetGain = values[values.length - 1] >= initialCapital;
        const strokeColor = isNetGain ? '#00E676' : '#FF3366';
        const fillGrad = ctx.createLinearGradient(0, padY, 0, padY + drawH);
        if (isNetGain) {
            fillGrad.addColorStop(0, 'rgba(0, 230, 118, 0.25)');
            fillGrad.addColorStop(1, 'rgba(0, 230, 118, 0.0)');
        } else {
            fillGrad.addColorStop(0, 'rgba(255, 51, 102, 0.25)');
            fillGrad.addColorStop(1, 'rgba(255, 51, 102, 0.0)');
        }

        ctx.beginPath();
        ctx.moveTo(getX(0), getY(values[0]));
        for (let i = 1; i < values.length; i++) {
            ctx.lineTo(getX(i), getY(values[i]));
        }
        ctx.lineTo(getX(values.length - 1), padY + drawH);
        ctx.lineTo(getX(0), padY + drawH);
        ctx.closePath();
        ctx.fillStyle = fillGrad;
        ctx.fill();

        // Stroke Equity Curve line with glowing neon aesthetic
        ctx.save();
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 2.5;
        ctx.shadowColor = strokeColor;
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.moveTo(getX(0), getY(values[0]));
        for (let i = 1; i < values.length; i++) {
            ctx.lineTo(getX(i), getY(values[i]));
        }
        ctx.stroke();
        ctx.restore();

        // Draw final point marker
        const lastX = getX(values.length - 1);
        const lastY = getY(values[values.length - 1]);
        ctx.beginPath();
        ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
        ctx.fillStyle = strokeColor;
        ctx.shadowColor = strokeColor;
        ctx.shadowBlur = 10;
        ctx.fill();
    }

    // =========================================================================
    // Institutional Paper Trading Engine & Terminal Controller
    // =========================================================================
}

class PaperTradingEngine {
    constructor(terminal) {
        this.terminal = terminal;
        this.balance = parseFloat(localStorage.getItem('tradeSignal_paper_balance') || '100000');
        this.positions = JSON.parse(localStorage.getItem('tradeSignal_paper_positions') || '[]');
        this.orders = JSON.parse(localStorage.getItem('tradeSignal_paper_orders') || '[]');
        this.history = JSON.parse(localStorage.getItem('tradeSignal_paper_history') || '[]');

        this.activeTab = 'positions';
        this.selectedMode = 'market';
        this.selectedSide = 'LONG';
        this.selectedLeverage = 1;
        this.selectedMargin = 10000;
        this.isCollapsed = false;

        // Chart line handles
        this.posPriceLine = null;
        this.tpPriceLine = null;
        this.slPriceLine = null;

        this.initDOM();
        this.updateUI();
    }

    initDOM() {
        this.dom = {
            // Dock elements
            dockEl: document.getElementById('paper-terminal-dock'),
            dockTabs: document.getElementById('dock-tabs'),
            tabPosCount: document.getElementById('pt-tab-pos-count'),
            tabOrdersCount: document.getElementById('pt-tab-orders-count'),
            tabHistCount: document.getElementById('pt-tab-hist-count'),
            dockEquity: document.getElementById('dock-equity'),
            dockAvailMargin: document.getElementById('dock-avail-margin'),
            dockUnrealizedPnl: document.getElementById('dock-unrealized-pnl'),
            btnDockReset: document.getElementById('btn-dock-reset'),
            btnDockExport: document.getElementById('btn-dock-export'),
            btnDockToggle: document.getElementById('btn-dock-toggle'),
            // Panels & tables
            tbodyPositions: document.getElementById('dock-positions-tbody'),
            tbodyOrders: document.getElementById('dock-orders-tbody'),
            tbodyHistory: document.getElementById('dock-history-tbody'),
            // Analytics
            winRate: document.getElementById('analytics-win-rate'),
            winCounts: document.getElementById('analytics-win-counts'),
            netPnl: document.getElementById('analytics-net-pnl'),
            grossFees: document.getElementById('analytics-gross-fees'),
            profitFactor: document.getElementById('analytics-profit-factor'),
            totalTrades: document.getElementById('analytics-total-trades'),
            openCount: document.getElementById('analytics-open-count'),
            avgReturn: document.getElementById('analytics-avg-return'),
            bestWorst: document.getElementById('analytics-best-worst'),
            // Pro Order Ticket
            ticketBalanceTag: document.getElementById('ticket-balance-tag'),
            orderModeTabs: document.getElementById('order-mode-tabs'),
            btnSideLong: document.getElementById('btn-side-long'),
            btnSideShort: document.getElementById('btn-side-short'),
            fieldPriceRow: document.getElementById('field-order-price-row'),
            inputPrice: document.getElementById('input-order-price'),
            lblOrderPrice: document.getElementById('lbl-order-price'),
            leverageChips: document.getElementById('leverage-chips'),
            inputMargin: document.getElementById('input-order-margin'),
            pctMarginLabel: document.getElementById('pct-margin-label'),
            marginPctChips: document.getElementById('margin-pct-chips'),
            inputTp: document.getElementById('input-order-tp'),
            inputSl: document.getElementById('input-order-sl'),
            btnCopySignal: document.getElementById('btn-copy-signal'),
            summaryNotional: document.getElementById('summary-notional'),
            summaryQty: document.getElementById('summary-qty'),
            summaryLiq: document.getElementById('summary-liq'),
            summaryFee: document.getElementById('summary-fee'),
            btnSubmitOrder: document.getElementById('btn-submit-order'),
            toastContainer: document.getElementById('paper-toast-container')
        };
    }

    saveState() {
        localStorage.setItem('tradeSignal_paper_balance', this.balance.toString());
        localStorage.setItem('tradeSignal_paper_positions', JSON.stringify(this.positions));
        localStorage.setItem('tradeSignal_paper_orders', JSON.stringify(this.orders));
        localStorage.setItem('tradeSignal_paper_history', JSON.stringify(this.history));
    }

    getUsedMargin() {
        const posMargin = this.positions.reduce((acc, p) => acc + (p.margin || 0), 0);
        const orderMargin = this.orders.reduce((acc, o) => acc + (o.margin || 0), 0);
        return posMargin + orderMargin;
    }

    getAvailableMargin() {
        return Math.max(0, this.balance - this.getUsedMargin());
    }

    getTotalUnrealizedPnL() {
        return this.positions.reduce((acc, p) => acc + (p.unrealizedPnl || 0), 0);
    }

    getEquity() {
        return this.balance + this.getTotalUnrealizedPnL();
    }

    calcLiqPrice(side, entryPrice, leverage) {
        if (!leverage || leverage <= 1) return null; // Spot / 1x has no liquidation
        if (side === 'LONG') {
            const liq = entryPrice * (1 - (1 / leverage) + 0.005);
            return Math.max(0, liq);
        } else {
            return entryPrice * (1 + (1 / leverage) - 0.005);
        }
    }

    bindEvents() {
        // 1. Dock Tab Switching
        if (this.dom.dockTabs) {
            this.dom.dockTabs.addEventListener('click', (e) => {
                const tabBtn = e.target.closest('.dock-tab');
                if (!tabBtn) return;
                const tab = tabBtn.dataset.tab;
                this.switchTab(tab);
            });
        }

        // 2. Dock Collapse Toggle
        if (this.dom.btnDockToggle) {
            this.dom.btnDockToggle.addEventListener('click', () => {
                this.isCollapsed = !this.isCollapsed;
                if (this.dom.dockEl) this.dom.dockEl.classList.toggle('collapsed', this.isCollapsed);
                this.dom.btnDockToggle.textContent = this.isCollapsed ? '▴' : '▾';
            });
        }

        // 3. Dock Reset Account
        if (this.dom.btnDockReset) {
            this.dom.btnDockReset.addEventListener('click', () => this.resetAccount());
        }

        // 4. Dock Export CSV
        if (this.dom.btnDockExport) {
            this.dom.btnDockExport.addEventListener('click', () => this.exportCSV());
        }

        // 5. Order Mode Switcher (Market / Limit / Stop)
        if (this.dom.orderModeTabs) {
            this.dom.orderModeTabs.addEventListener('click', (e) => {
                const btn = e.target.closest('.order-mode-btn');
                if (!btn) return;
                this.dom.orderModeTabs.querySelectorAll('.order-mode-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.selectedMode = btn.dataset.mode;
                
                if (this.dom.fieldPriceRow) {
                    if (this.selectedMode === 'market') {
                        this.dom.fieldPriceRow.classList.add('hidden');
                    } else {
                        this.dom.fieldPriceRow.classList.remove('hidden');
                        if (this.dom.lblOrderPrice) {
                            this.dom.lblOrderPrice.textContent = this.selectedMode === 'limit' ? 'Limit Price ($):' : 'Stop Trigger ($):';
                        }
                        if (this.dom.inputPrice && (!this.dom.inputPrice.value || parseFloat(this.dom.inputPrice.value) === 0)) {
                            this.dom.inputPrice.value = this.terminal.latestPrice || '';
                        }
                    }
                }
                this.updateSubmitButtonLabel();
                this.updateTicketSummary();
            });
        }

        // 6. Side Switcher (LONG vs SHORT)
        if (this.dom.btnSideLong) {
            this.dom.btnSideLong.addEventListener('click', () => {
                this.selectedSide = 'LONG';
                this.updateSideButtons();
                this.updateTicketSummary();
            });
        }
        if (this.dom.btnSideShort) {
            this.dom.btnSideShort.addEventListener('click', () => {
                this.selectedSide = 'SHORT';
                this.updateSideButtons();
                this.updateTicketSummary();
            });
        }

        // 7. Leverage Selector
        if (this.dom.leverageChips) {
            this.dom.leverageChips.addEventListener('click', (e) => {
                const chip = e.target.closest('.lev-chip');
                if (!chip) return;
                this.dom.leverageChips.querySelectorAll('.lev-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                this.selectedLeverage = parseInt(chip.dataset.lev, 10) || 1;
                this.updateTicketSummary();
            });
        }

        // 8. Margin Input & Percentage Quick-Chips
        if (this.dom.inputMargin) {
            this.dom.inputMargin.addEventListener('input', () => {
                this.selectedMargin = parseFloat(this.dom.inputMargin.value) || 0;
                if (this.dom.pctMarginLabel) {
                    const avail = this.getAvailableMargin();
                    const pct = avail > 0 ? ((this.selectedMargin / avail) * 100).toFixed(0) : '0';
                    this.dom.pctMarginLabel.textContent = `${pct}% of Avail`;
                }
                this.updateTicketSummary();
            });
        }

        if (this.dom.marginPctChips) {
            this.dom.marginPctChips.addEventListener('click', (e) => {
                const chip = e.target.closest('.pct-chip');
                if (!chip) return;
                this.dom.marginPctChips.querySelectorAll('.pct-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                const pct = parseFloat(chip.dataset.pct);
                const avail = this.getAvailableMargin();
                this.selectedMargin = Math.max(10, Math.floor(avail * pct));
                if (this.dom.inputMargin) {
                    this.dom.inputMargin.value = this.selectedMargin.toFixed(0);
                }
                if (this.dom.pctMarginLabel) {
                    this.dom.pctMarginLabel.textContent = `${(pct * 100).toFixed(0)}% of Avail`;
                }
                this.updateTicketSummary();
            });
        }

        // 9. Limit Price Input change
        if (this.dom.inputPrice) {
            this.dom.inputPrice.addEventListener('input', () => this.updateTicketSummary());
        }

        // 10. Copy Signal Targets (Auto-fill TP & SL from dynamic ATR/ML forecast)
        if (this.dom.btnCopySignal) {
            this.dom.btnCopySignal.addEventListener('click', () => this.copySignalTargets());
        }

        // 11. Place Order Button
        if (this.dom.btnSubmitOrder) {
            this.dom.btnSubmitOrder.addEventListener('click', () => this.executeOrder());
        }
    }

    switchTab(tab) {
        this.activeTab = tab;
        if (this.dom.dockTabs) {
            this.dom.dockTabs.querySelectorAll('.dock-tab').forEach(b => {
                b.classList.toggle('active', b.dataset.tab === tab);
            });
        }
        document.querySelectorAll('.dock-panel').forEach(panel => {
            panel.classList.toggle('active', panel.id === `dock-panel-${tab}`);
        });
        if (tab === 'news' && this.terminal) {
            this.terminal.loadNewsData();
        } else if (tab === 'backtest' && this.terminal) {
            this.terminal.loadBacktestData();
            setTimeout(() => this.terminal.resizeChart(), 100);
        }
        this.updateUI();
    }

    updateSideButtons() {
        if (this.dom.btnSideLong) this.dom.btnSideLong.classList.toggle('active', this.selectedSide === 'LONG');
        if (this.dom.btnSideShort) this.dom.btnSideShort.classList.toggle('active', this.selectedSide === 'SHORT');
        this.updateSubmitButtonLabel();
    }

    updateSubmitButtonLabel() {
        if (!this.dom.btnSubmitOrder) return;
        const modeText = this.selectedMode.charAt(0).toUpperCase() + this.selectedMode.slice(1);
        const sideText = this.selectedSide;
        this.dom.btnSubmitOrder.textContent = `⚡ Place ${modeText} ${sideText} Order`;
        this.dom.btnSubmitOrder.className = `btn-submit-order side-${this.selectedSide.toLowerCase()}`;
    }

    setLimitPrice(price, side = null) {
        if (side) {
            this.selectedSide = (side === 'BUY' || side === 'LONG') ? 'LONG' : 'SHORT';
            this.updateSideButtons();
        }
        if (this.dom.orderModeTabs) {
            this.dom.orderModeTabs.querySelectorAll('.order-mode-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.mode === 'limit');
            });
            this.selectedMode = 'limit';
            if (this.dom.fieldPriceRow) {
                this.dom.fieldPriceRow.classList.remove('hidden');
                if (this.dom.lblOrderPrice) this.dom.lblOrderPrice.textContent = 'Limit Price ($):';
            }
        }
        if (this.dom.inputPrice) {
            this.dom.inputPrice.value = price;
            this.dom.inputPrice.classList.add('flash-input');
            setTimeout(() => this.dom.inputPrice.classList.remove('flash-input'), 800);
        }
        this.updateSubmitButtonLabel();
        this.updateTicketSummary();
        this.switchTab('positions');
        this.showToast('fill', 'DOM Price Staged', `Limit ${this.selectedSide} @ $${price > 10 ? price.toLocaleString(undefined, {minimumFractionDigits: 2}) : price}`);
    }

    copySignalTargets() {
        const targets = this.terminal.cachedTargets;
        if (!targets || (!targets.tp && !targets.sl)) {
            this.showToast('info', 'No Active Signal Targets', 'Awaiting market target calculation...');
            return;
        }

        if (this.dom.inputTp && targets.tp) {
            this.dom.inputTp.value = targets.tp > 10 ? targets.tp.toFixed(2) : targets.tp.toFixed(4);
        }
        if (this.dom.inputSl && targets.sl) {
            this.dom.inputSl.value = targets.sl > 10 ? targets.sl.toFixed(2) : targets.sl.toFixed(4);
        }

        // If active quant signal is SELL, switch to SHORT; if BUY, switch to LONG
        const curSig = document.getElementById('signal-action-badge');
        if (curSig) {
            const sigText = curSig.textContent.trim().toUpperCase();
            if (sigText === 'SELL' && this.selectedSide !== 'SHORT') {
                this.selectedSide = 'SHORT';
                this.updateSideButtons();
            } else if (sigText === 'BUY' && this.selectedSide !== 'LONG') {
                this.selectedSide = 'LONG';
                this.updateSideButtons();
            }
        }

        this.showToast('fill', 'Signal Copied', `Loaded TP: $${targets.tp} | SL: $${targets.sl}`);
    }

    updateTicketSummary() {
        const curPrice = this.terminal.latestPrice || 1;
        const orderPrice = (this.selectedMode !== 'market' && this.dom.inputPrice && parseFloat(this.dom.inputPrice.value) > 0)
            ? parseFloat(this.dom.inputPrice.value)
            : curPrice;

        const margin = parseFloat(this.dom.inputMargin ? this.dom.inputMargin.value : '10000') || 10000;
        const leverage = this.selectedLeverage;
        const notional = margin * leverage;
        const qty = orderPrice > 0 ? (notional / orderPrice) : 0;
        const takerFee = notional * 0.0004;
        const liqPrice = this.calcLiqPrice(this.selectedSide, orderPrice, leverage);

        if (this.dom.summaryNotional) this.dom.summaryNotional.textContent = `$${notional.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        if (this.dom.summaryQty) {
            const cleanSym = (this.terminal.activeSymbol || 'BTC').replace('-USD', '');
            this.dom.summaryQty.textContent = `${qty.toFixed(4)} ${cleanSym}`;
        }
        if (this.dom.summaryLiq) {
            if (liqPrice === null || leverage <= 1) {
                this.dom.summaryLiq.textContent = 'None (Spot 1x)';
                this.dom.summaryLiq.className = 'liq-safe';
            } else {
                const liqFormatted = liqPrice > 10 ? liqPrice.toLocaleString(undefined, { minimumFractionDigits: 2 }) : liqPrice.toFixed(4);
                this.dom.summaryLiq.textContent = `$${liqFormatted}`;
                this.dom.summaryLiq.className = 'liq-risk';
            }
        }
        if (this.dom.summaryFee) this.dom.summaryFee.textContent = `$${takerFee.toFixed(2)}`;
    }

    executeOrder() {
        const curPrice = this.terminal.latestPrice;
        if (!curPrice || curPrice <= 0) {
            this.showToast('sl', 'Pricing Tick Required', 'Waiting for valid live market feed...');
            return;
        }

        const margin = parseFloat(this.dom.inputMargin ? this.dom.inputMargin.value : '0') || 0;
        const avail = this.getAvailableMargin();

        if (margin <= 0) {
            this.showToast('sl', 'Invalid Margin', 'Please specify margin allocation greater than 0.');
            return;
        }

        if (margin > avail) {
            this.showToast('sl', 'Insufficient Margin', `Available margin is $${avail.toFixed(2)}, requested $${margin.toFixed(2)}.`);
            return;
        }

        const leverage = this.selectedLeverage;
        const notional = margin * leverage;
        const cleanSym = this.terminal.activeSymbol.replace('-USD', '');
        const tp = parseFloat(this.dom.inputTp ? this.dom.inputTp.value : '0') || 0;
        const sl = parseFloat(this.dom.inputSl ? this.dom.inputSl.value : '0') || 0;
        const nowTime = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

        if (this.selectedMode === 'market') {
            const qty = notional / curPrice;
            const takerFee = notional * 0.0004;
            this.balance -= takerFee; // Taker execution fee

            const pos = {
                id: 'POS-' + Math.random().toString(36).substring(2, 8).toUpperCase(),
                symbol: this.terminal.activeSymbol,
                side: this.selectedSide,
                qty: qty,
                entryPrice: curPrice,
                markPrice: curPrice,
                margin: margin,
                leverage: leverage,
                notional: notional,
                liqPrice: this.calcLiqPrice(this.selectedSide, curPrice, leverage),
                tp: tp,
                sl: sl,
                unrealizedPnl: 0,
                unrealizedPnlPct: 0,
                openTime: nowTime
            };

            this.positions.push(pos);
            this.saveState();
            this.showToast('fill', `Market ${pos.side} Filled`, `${qty.toFixed(4)} ${cleanSym} @ $${curPrice > 10 ? curPrice.toFixed(2) : curPrice.toFixed(4)}`);
            this.updateUI();
            this.updateChartPositionLines();

        } else {
            // Limit or Stop Order
            const targetPrice = parseFloat(this.dom.inputPrice ? this.dom.inputPrice.value : '0');
            if (!targetPrice || targetPrice <= 0) {
                this.showToast('sl', 'Invalid Order Price', 'Please enter a valid price for limit/stop execution.');
                return;
            }

            const qty = notional / targetPrice;
            const order = {
                id: 'ORD-' + Math.random().toString(36).substring(2, 8).toUpperCase(),
                symbol: this.terminal.activeSymbol,
                orderType: this.selectedMode.toUpperCase(),
                side: this.selectedSide,
                targetPrice: targetPrice,
                qty: qty,
                margin: margin,
                leverage: leverage,
                tp: tp,
                sl: sl,
                createdTime: nowTime
            };

            this.orders.push(order);
            this.saveState();
            this.showToast('fill', `${order.orderType} Order Placed`, `${order.side} ${qty.toFixed(4)} ${cleanSym} @ $${targetPrice}`);
            this.updateUI();
        }
    }

    onPriceTick(symbol, curPrice, candles) {
        if (!curPrice || curPrice <= 0) return;

        let stateChanged = false;

        // 1. Process Pending Limit & Stop Orders
        for (let i = this.orders.length - 1; i >= 0; i--) {
            const ord = this.orders[i];
            if (ord.symbol !== symbol) continue;

            let filled = false;
            if (ord.orderType === 'LIMIT') {
                if (ord.side === 'LONG' && curPrice <= ord.targetPrice) filled = true;
                if (ord.side === 'SHORT' && curPrice >= ord.targetPrice) filled = true;
            } else if (ord.orderType === 'STOP') {
                if (ord.side === 'LONG' && curPrice >= ord.targetPrice) filled = true;
                if (ord.side === 'SHORT' && curPrice <= ord.targetPrice) filled = true;
            }

            if (filled) {
                const notional = ord.margin * ord.leverage;
                const fillPrice = ord.targetPrice;
                const qty = notional / fillPrice;
                const fee = notional * 0.0004;
                this.balance -= fee;

                const newPos = {
                    id: 'POS-' + Math.random().toString(36).substring(2, 8).toUpperCase(),
                    symbol: ord.symbol,
                    side: ord.side,
                    qty: qty,
                    entryPrice: fillPrice,
                    markPrice: curPrice,
                    margin: ord.margin,
                    leverage: ord.leverage,
                    notional: notional,
                    liqPrice: this.calcLiqPrice(ord.side, fillPrice, ord.leverage),
                    tp: ord.tp,
                    sl: ord.sl,
                    unrealizedPnl: 0,
                    unrealizedPnlPct: 0,
                    openTime: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                };

                this.positions.push(newPos);
                this.orders.splice(i, 1);
                stateChanged = true;
                this.showToast('fill', `Order Triggered & Filled`, `${ord.side} ${qty.toFixed(4)} @ $${fillPrice}`);
            }
        }

        // 2. Process Active Positions (PnL, TP, SL, Liquidation)
        for (let i = this.positions.length - 1; i >= 0; i--) {
            const pos = this.positions[i];
            if (pos.symbol !== symbol) continue;

            pos.markPrice = curPrice;
            const priceDiff = pos.side === 'LONG' ? (curPrice - pos.entryPrice) : (pos.entryPrice - curPrice);
            pos.unrealizedPnl = priceDiff * pos.qty;
            pos.unrealizedPnlPct = (pos.unrealizedPnl / pos.margin) * 100;

            // Check Liquidation
            if (pos.liqPrice) {
                let liquidated = false;
                if (pos.side === 'LONG' && curPrice <= pos.liqPrice) liquidated = true;
                if (pos.side === 'SHORT' && curPrice >= pos.liqPrice) liquidated = true;
                if (liquidated) {
                    this.closePosition(pos.id, pos.liqPrice, 'Liquidated 💀');
                    stateChanged = true;
                    continue;
                }
            }

            // Check Take Profit Trigger
            if (pos.tp && pos.tp > 0) {
                let tpHit = false;
                if (pos.side === 'LONG' && curPrice >= pos.tp) tpHit = true;
                if (pos.side === 'SHORT' && curPrice <= pos.tp) tpHit = true;
                if (tpHit) {
                    this.closePosition(pos.id, pos.tp, 'Take Profit Hit 🎯');
                    stateChanged = true;
                    continue;
                }
            }

            // Check Stop Loss Trigger
            if (pos.sl && pos.sl > 0) {
                let slHit = false;
                if (pos.side === 'LONG' && curPrice <= pos.sl) slHit = true;
                if (pos.side === 'SHORT' && curPrice >= pos.sl) slHit = true;
                if (slHit) {
                    this.closePosition(pos.id, pos.sl, 'Stop Loss Triggered 🛡️');
                    stateChanged = true;
                    continue;
                }
            }
        }

        this.updateUI();
        if (symbol === this.terminal.activeSymbol) {
            this.updateChartPositionLines();
        }
        if (stateChanged) {
            this.saveState();
        }
    }

    closePosition(posId, exitPrice = null, reason = 'Manual Market Close') {
        const idx = this.positions.findIndex(p => p.id === posId);
        if (idx === -1) return;

        const pos = this.positions[idx];
        const actualExit = exitPrice || pos.markPrice || pos.entryPrice;
        const priceDiff = pos.side === 'LONG' ? (actualExit - pos.entryPrice) : (pos.entryPrice - actualExit);
        const grossPnl = priceDiff * pos.qty;
        const exitFee = (pos.qty * actualExit) * 0.0004;
        const netPnl = grossPnl - exitFee;

        // Return initial margin + realized PnL
        this.balance += (pos.margin + netPnl);

        const closedRecord = {
            id: pos.id,
            symbol: pos.symbol,
            side: pos.side,
            entryTime: pos.openTime,
            exitTime: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            entryPrice: pos.entryPrice,
            exitPrice: actualExit,
            qty: pos.qty,
            margin: pos.margin,
            netPnl: netPnl,
            returnPct: (netPnl / pos.margin) * 100,
            reason: reason
        };

        this.history.unshift(closedRecord);
        this.positions.splice(idx, 1);
        this.saveState();

        const toastType = netPnl >= 0 ? 'tp' : 'sl';
        const sign = netPnl >= 0 ? '+' : '';
        this.showToast(toastType, `${reason}`, `${pos.symbol.replace('-USD','')} ${pos.side} closed: ${sign}$${netPnl.toFixed(2)} (${sign}${closedRecord.returnPct.toFixed(2)}%)`);

        if (netPnl > 0 && this.terminal.wsManager) {
            this.terminal.wsManager.playSuccessChime();
        }

        this.updateUI();
        this.updateChartPositionLines();
    }

    reversePosition(posId) {
        const pos = this.positions.find(p => p.id === posId);
        if (!pos) return;
        const curPrice = pos.markPrice;
        const margin = pos.margin;
        const leverage = pos.leverage;
        const newSide = pos.side === 'LONG' ? 'SHORT' : 'LONG';

        this.closePosition(posId, curPrice, 'Reversed ⇄');
        
        // Open opposite position immediately
        this.selectedSide = newSide;
        this.selectedLeverage = leverage;
        if (this.dom.inputMargin) this.dom.inputMargin.value = margin.toString();
        this.executeOrder();
    }

    cancelOrder(orderId) {
        const idx = this.orders.findIndex(o => o.id === orderId);
        if (idx === -1) return;
        const ord = this.orders[idx];
        this.orders.splice(idx, 1);
        this.saveState();
        this.showToast('info', 'Order Cancelled', `Removed ${ord.orderType} order for ${ord.symbol.replace('-USD','')}`);
        this.updateUI();
    }

    closeAllPositions() {
        if (this.positions.length === 0) {
            this.showToast('info', 'No Open Positions', 'Zero active positions to close.');
            return;
        }
        const count = this.positions.length;
        while (this.positions.length > 0) {
            this.closePosition(this.positions[0].id, null, 'Close All Action');
        }
        this.showToast('info', 'All Closed', `Successfully closed ${count} active positions.`);
    }

    resetAccount() {
        if (!confirm('Are you sure you want to reset your paper trading account to $100,000? All active positions and journal history will be cleared.')) {
            return;
        }
        this.balance = 100000;
        this.positions = [];
        this.orders = [];
        this.history = [];
        this.saveState();
        this.showToast('fill', 'Account Reset', 'Balance restored to $100,000.00 virtual equity.');
        this.updateUI();
        this.updateChartPositionLines();
    }

    exportCSV() {
        if (this.history.length === 0) {
            alert('No closed trades in journal to export yet.');
            return;
        }

        let csv = 'ID,Symbol,Side,EntryTime,ExitTime,EntryPrice,ExitPrice,Qty,Margin,NetPnL,ReturnPct,Reason\n';
        this.history.forEach(h => {
            csv += `"${h.id}","${h.symbol}","${h.side}","${h.entryTime}","${h.exitTime}",${h.entryPrice},${h.exitPrice},${h.qty.toFixed(6)},${h.margin.toFixed(2)},${h.netPnl.toFixed(2)},${h.returnPct.toFixed(2)},"${h.reason}"\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tradesignal_paper_journal_${new Date().toISOString().slice(0,10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    showToast(type, title, msg) {
        if (!this.dom.toastContainer) return;
        const toast = document.createElement('div');
        toast.className = `paper-toast toast-${type}`;
        
        const icon = type === 'tp' ? '🎯' : (type === 'sl' ? '🛡️' : (type === 'fill' ? '⚡' : 'ℹ️'));
        toast.innerHTML = `
            <span class="toast-icon">${icon}</span>
            <div class="toast-content">
                <span class="toast-title">${title}</span>
                <span class="toast-msg">${msg}</span>
            </div>
        `;
        this.dom.toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 250);
        }, 4000);
    }

    updateUI() {
        // 1. Header & Quick Metric Pills
        const equity = this.getEquity();
        const avail = this.getAvailableMargin();
        const upnl = this.getTotalUnrealizedPnL();
        const upnlPct = this.balance > 0 ? (upnl / this.balance) * 100 : 0;
        const sign = upnl >= 0 ? '+' : '';
        const pnlClass = upnl > 0 ? 'pos' : (upnl < 0 ? 'neg' : 'neutral');

        if (this.dom.dockEquity) this.dom.dockEquity.textContent = `$${equity.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        if (this.dom.dockAvailMargin) this.dom.dockAvailMargin.textContent = `$${avail.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        if (this.dom.dockUnrealizedPnl) {
            this.dom.dockUnrealizedPnl.textContent = `${sign}$${upnl.toFixed(2)} (${sign}${upnlPct.toFixed(2)}%)`;
            this.dom.dockUnrealizedPnl.className = `pill-val ${pnlClass}`;
        }
        if (this.dom.ticketBalanceTag) {
            this.dom.ticketBalanceTag.textContent = `$${equity.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }

        // 2. Tab Badges
        if (this.dom.tabPosCount) this.dom.tabPosCount.textContent = this.positions.length.toString();
        if (this.dom.tabOrdersCount) this.dom.tabOrdersCount.textContent = this.orders.length.toString();
        if (this.dom.tabHistCount) this.dom.tabHistCount.textContent = this.history.length.toString();

        // 3. Render Table for Active Tab
        if (this.activeTab === 'positions') this.renderPositionsTable();
        else if (this.activeTab === 'orders') this.renderOrdersTable();
        else if (this.activeTab === 'history') this.renderHistoryTable();
        else if (this.activeTab === 'analytics') this.renderAnalytics();

        this.updateTicketSummary();
    }

    renderPositionsTable() {
        if (!this.dom.tbodyPositions) return;
        if (this.positions.length === 0) {
            this.dom.tbodyPositions.innerHTML = `
                <tr class="table-empty-row">
                    <td colspan="11">No active positions. Execute orders from the Pro Order Ticket to open positions.</td>
                </tr>
            `;
            return;
        }

        let html = '';
        this.positions.forEach(pos => {
            const cleanSym = pos.symbol.replace('-USD', '');
            const sign = pos.unrealizedPnl >= 0 ? '+' : '';
            const pnlClass = pos.unrealizedPnl >= 0 ? 'pos' : 'neg';
            const liqFormatted = pos.liqPrice ? `$${pos.liqPrice > 10 ? pos.liqPrice.toLocaleString(undefined, { minimumFractionDigits: 2 }) : pos.liqPrice.toFixed(4)}` : '<span style="color:#536079">None</span>';
            const tpFormatted = pos.tp > 0 ? `$${pos.tp}` : '-';
            const slFormatted = pos.sl > 0 ? `$${pos.sl}` : '-';

            html += `
                <tr>
                    <td><b>${cleanSym}</b></td>
                    <td><span class="side-badge ${pos.side.toLowerCase()}">${pos.side}</span></td>
                    <td>${pos.qty.toFixed(4)}</td>
                    <td>$${pos.notional.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td>$${pos.entryPrice > 10 ? pos.entryPrice.toLocaleString(undefined, { minimumFractionDigits: 2 }) : pos.entryPrice.toFixed(4)}</td>
                    <td>$${pos.markPrice > 10 ? pos.markPrice.toLocaleString(undefined, { minimumFractionDigits: 2 }) : pos.markPrice.toFixed(4)}</td>
                    <td>${liqFormatted}</td>
                    <td>$${pos.margin.toLocaleString(undefined, { minimumFractionDigits: 2 })} (${pos.leverage}x)</td>
                    <td>${tpFormatted} / ${slFormatted}</td>
                    <td class="tbl-pnl-cell ${pnlClass}">${sign}$${pos.unrealizedPnl.toFixed(2)} (${sign}${pos.unrealizedPnlPct.toFixed(2)}%)</td>
                    <td style="text-align: right;">
                        <button class="tbl-btn-action btn-reverse" onclick="terminal.paper.reversePosition('${pos.id}')" title="Reverse position side">⇄</button>
                        <button class="tbl-btn-action" onclick="terminal.paper.closePosition('${pos.id}')" title="Close position at market price">✕ Close</button>
                    </td>
                </tr>
            `;
        });
        this.dom.tbodyPositions.innerHTML = html;
    }

    renderOrdersTable() {
        if (!this.dom.tbodyOrders) return;
        if (this.orders.length === 0) {
            this.dom.tbodyOrders.innerHTML = `
                <tr class="table-empty-row">
                    <td colspan="11">No open limit or stop orders. Set a limit price in the order ticket to stage orders.</td>
                </tr>
            `;
            return;
        }

        let html = '';
        this.orders.forEach(ord => {
            const cleanSym = ord.symbol.replace('-USD', '');
            const curPrice = this.terminal.latestPrice || 0;
            const tpFormatted = ord.tp > 0 ? `$${ord.tp}` : '-';
            const slFormatted = ord.sl > 0 ? `$${ord.sl}` : '-';

            html += `
                <tr>
                    <td><code>${ord.id}</code></td>
                    <td><b>${cleanSym}</b></td>
                    <td><span class="side-badge">${ord.orderType}</span></td>
                    <td><span class="side-badge ${ord.side.toLowerCase()}">${ord.side}</span></td>
                    <td>$${ord.targetPrice > 10 ? ord.targetPrice.toLocaleString(undefined, { minimumFractionDigits: 2 }) : ord.targetPrice.toFixed(4)}</td>
                    <td>$${curPrice > 10 ? curPrice.toLocaleString(undefined, { minimumFractionDigits: 2 }) : curPrice.toFixed(4)}</td>
                    <td>${ord.qty.toFixed(4)}</td>
                    <td>$${ord.margin.toLocaleString(undefined, { minimumFractionDigits: 2 })} (${ord.leverage}x)</td>
                    <td>${tpFormatted} / ${slFormatted}</td>
                    <td>${ord.createdTime}</td>
                    <td style="text-align: right;">
                        <button class="tbl-btn-action" onclick="terminal.paper.cancelOrder('${ord.id}')">✕ Cancel</button>
                    </td>
                </tr>
            `;
        });
        this.dom.tbodyOrders.innerHTML = html;
    }

    renderHistoryTable() {
        if (!this.dom.tbodyHistory) return;
        if (this.history.length === 0) {
            this.dom.tbodyHistory.innerHTML = `
                <tr class="table-empty-row">
                    <td colspan="9">No closed trades yet. Your trade performance journal will appear here upon closing positions.</td>
                </tr>
            `;
            return;
        }

        let html = '';
        this.history.slice(0, 50).forEach(h => {
            const cleanSym = h.symbol.replace('-USD', '');
            const sign = h.netPnl >= 0 ? '+' : '';
            const pnlClass = h.netPnl >= 0 ? 'pos' : 'neg';

            html += `
                <tr>
                    <td><b>${cleanSym}</b></td>
                    <td><span class="side-badge ${h.side.toLowerCase()}">${h.side}</span></td>
                    <td>${h.entryTime}</td>
                    <td>${h.exitTime}</td>
                    <td>$${h.entryPrice > 10 ? h.entryPrice.toLocaleString(undefined, { minimumFractionDigits: 2 }) : h.entryPrice.toFixed(4)}</td>
                    <td>$${h.exitPrice > 10 ? h.exitPrice.toLocaleString(undefined, { minimumFractionDigits: 2 }) : h.exitPrice.toFixed(4)}</td>
                    <td class="tbl-pnl-cell ${pnlClass}">${sign}$${h.netPnl.toFixed(2)}</td>
                    <td class="tbl-pnl-cell ${pnlClass}">${sign}${h.returnPct.toFixed(2)}%</td>
                    <td><span class="side-badge">${h.reason}</span></td>
                </tr>
            `;
        });
        this.dom.tbodyHistory.innerHTML = html;
    }

    renderAnalytics() {
        const total = this.history.length;
        const wins = this.history.filter(h => h.netPnl > 0);
        const losses = this.history.filter(h => h.netPnl <= 0);
        const winCount = wins.length;
        const lossCount = losses.length;
        const winRate = total > 0 ? ((winCount / total) * 100).toFixed(1) : '0.0';

        const totalNetPnl = this.history.reduce((acc, h) => acc + h.netPnl, 0);
        const grossWins = wins.reduce((acc, h) => acc + h.netPnl, 0);
        const grossLosses = Math.abs(losses.reduce((acc, h) => acc + h.netPnl, 0));
        const profitFactor = grossLosses > 0 ? (grossWins / grossLosses).toFixed(2) : (grossWins > 0 ? 'MAX' : '0.00');

        const avgReturn = total > 0 ? (this.history.reduce((acc, h) => acc + h.returnPct, 0) / total).toFixed(2) : '0.00';
        
        let best = 0;
        let worst = 0;
        this.history.forEach(h => {
            if (h.netPnl > best) best = h.netPnl;
            if (h.netPnl < worst) worst = h.netPnl;
        });

        if (this.dom.winRate) this.dom.winRate.textContent = `${winRate}%`;
        if (this.dom.winCounts) this.dom.winCounts.textContent = `${winCount} Wins / ${lossCount} Losses`;
        if (this.dom.netPnl) {
            const sign = totalNetPnl >= 0 ? '+' : '';
            this.dom.netPnl.textContent = `${sign}$${totalNetPnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            this.dom.netPnl.style.color = totalNetPnl >= 0 ? 'var(--neon-green)' : 'var(--neon-red)';
        }
        if (this.dom.grossFees) {
            const fees = total * 8; // approx
            this.dom.grossFees.textContent = `Realized Trades: ${total}`;
        }
        if (this.dom.profitFactor) this.dom.profitFactor.textContent = profitFactor;
        if (this.dom.totalTrades) this.dom.totalTrades.textContent = total.toString();
        if (this.dom.openCount) this.dom.openCount.textContent = `${this.positions.length} Open Positions`;
        if (this.dom.avgReturn) this.dom.avgReturn.textContent = `${avgReturn}%`;
        if (this.dom.bestWorst) this.dom.bestWorst.textContent = `+$${best.toFixed(0)} / -$${Math.abs(worst).toFixed(0)}`;
    }

    updateChartPositionLines() {
        if (!this.terminal.candlestickSeries) return;

        // Clean up previous position lines
        if (this.posPriceLine) {
            try { this.terminal.candlestickSeries.removePriceLine(this.posPriceLine); } catch (e) {}
            this.posPriceLine = null;
        }
        if (this.tpPriceLine) {
            try { this.terminal.candlestickSeries.removePriceLine(this.tpPriceLine); } catch (e) {}
            this.tpPriceLine = null;
        }
        if (this.slPriceLine) {
            try { this.terminal.candlestickSeries.removePriceLine(this.slPriceLine); } catch (e) {}
            this.slPriceLine = null;
        }

        // Find active position for current viewed symbol
        const activePos = this.positions.find(p => p.symbol === this.terminal.activeSymbol);
        if (!activePos) return;

        const sign = activePos.unrealizedPnl >= 0 ? '+' : '';
        const title = `POS: ${activePos.side} ${activePos.qty.toFixed(3)} @ $${activePos.entryPrice} (${sign}$${activePos.unrealizedPnl.toFixed(2)})`;
        const color = activePos.unrealizedPnl >= 0 ? '#00E676' : '#FF3366';

        this.posPriceLine = this.terminal.candlestickSeries.createPriceLine({
            price: activePos.entryPrice,
            color: '#00F2FE',
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Solid,
            axisLabelVisible: true,
            title: title
        });

        if (activePos.tp && activePos.tp > 0) {
            this.tpPriceLine = this.terminal.candlestickSeries.createPriceLine({
                price: activePos.tp,
                color: '#00E676',
                lineWidth: 1.5,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: `POS TP: $${activePos.tp}`
            });
        }

        if (activePos.sl && activePos.sl > 0) {
            this.slPriceLine = this.terminal.candlestickSeries.createPriceLine({
                price: activePos.sl,
                color: '#FF3366',
                lineWidth: 1.5,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: `POS SL: $${activePos.sl}`
            });
        }
    }

    // =========================================================================
    // Institutional Command Palette (Ctrl+K or /)
    // =========================================================================

    initCommandPalette() {
        if (!this.dom.btnOpenCmd || !this.dom.cmdBackdrop) return;

        const openCmd = () => {
            this.dom.cmdBackdrop.classList.remove('hidden');
            if (this.dom.cmdInput) {
                this.dom.cmdInput.value = '';
                this.dom.cmdInput.focus();
            }
            this.renderCommandPalette('');
        };

        const closeCmd = () => {
            this.dom.cmdBackdrop.classList.add('hidden');
        };

        this.dom.btnOpenCmd.addEventListener('click', openCmd);
        if (this.dom.cmdCloseEsc) {
            this.dom.cmdCloseEsc.addEventListener('click', closeCmd);
        }

        this.dom.cmdBackdrop.addEventListener('click', (e) => {
            if (e.target === this.dom.cmdBackdrop) closeCmd();
        });

        // Global hotkey listener: Ctrl+K, Cmd+K, or /
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                this.dom.cmdBackdrop.classList.contains('hidden') ? openCmd() : closeCmd();
            } else if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
                e.preventDefault();
                openCmd();
            } else if (e.key === 'Escape' && !this.dom.cmdBackdrop.classList.contains('hidden')) {
                closeCmd();
            }
        });

        if (this.dom.cmdInput) {
            this.dom.cmdInput.addEventListener('input', (e) => {
                this.renderCommandPalette(e.target.value);
            });
        }
    }

    getCommandList() {
        return [
            // Symbols
            { category: 'SYMBOL', text: 'Bitcoin (BTC-USD)', action: 'symbol', param: 'BTC-USD' },
            { category: 'SYMBOL', text: 'Ethereum (ETH-USD)', action: 'symbol', param: 'ETH-USD' },
            { category: 'SYMBOL', text: 'Solana (SOL-USD)', action: 'symbol', param: 'SOL-USD' },
            { category: 'SYMBOL', text: 'XRP (XRP-USD)', action: 'symbol', param: 'XRP-USD' },
            { category: 'SYMBOL', text: 'Dogecoin (DOGE-USD)', action: 'symbol', param: 'DOGE-USD' },
            { category: 'SYMBOL', text: 'Cardano (ADA-USD)', action: 'symbol', param: 'ADA-USD' },
            { category: 'SYMBOL', text: 'BNB (BNB-USD)', action: 'symbol', param: 'BNB-USD' },
            { category: 'EQUITY', text: 'Reliance Industries (RELIANCE.NS)', action: 'symbol', param: 'RELIANCE.NS' },
            { category: 'EQUITY', text: 'Tata Consultancy Services (TCS.NS)', action: 'symbol', param: 'TCS.NS' },
            { category: 'EQUITY', text: 'Infosys (INFY.NS)', action: 'symbol', param: 'INFY.NS' },
            // Timeframes
            { category: 'TIMEFRAME', text: 'Switch to 1-Minute (1M)', action: 'tf', param: '1m' },
            { category: 'TIMEFRAME', text: 'Switch to 5-Minute (5M)', action: 'tf', param: '5m' },
            { category: 'TIMEFRAME', text: 'Switch to 15-Minute (15M)', action: 'tf', param: '15m' },
            { category: 'TIMEFRAME', text: 'Switch to 1-Hour (1H)', action: 'tf', param: '1h' },
            { category: 'TIMEFRAME', text: 'Switch to 4-Hour (4H)', action: 'tf', param: '4h' },
            { category: 'TIMEFRAME', text: 'Switch to 1-Day (1D)', action: 'tf', param: '1d' },
            // AI / ML Models
            { category: 'AI MODEL', text: 'Activate Quant ML (Gradient Boosted Ensemble)', action: 'model', param: 'ml' },
            { category: 'AI MODEL', text: 'Activate Deep Learning (PyTorch LSTM)', action: 'model', param: 'dl' },
            { category: 'AI MODEL', text: 'Run Fresh AI / ML Inference (Current Asset)', action: 'run_infer', param: null },
            // Forecast Horizons
            { category: 'HORIZON', text: 'Set ML Horizon: 1 Bar Forward', action: 'horizon', param: 1 },
            { category: 'HORIZON', text: 'Set ML Horizon: 3 Bars Forward', action: 'horizon', param: 3 },
            { category: 'HORIZON', text: 'Set ML Horizon: 5 Bars Forward', action: 'horizon', param: 5 },
            { category: 'HORIZON', text: 'Set ML Horizon: 10 Bars Forward', action: 'horizon', param: 10 },
            // Strategies
            { category: 'STRATEGY', text: 'Preset: Holy Trinity (EMA + RSI + BB)', action: 'preset', param: 'holy_trinity' },
            { category: 'STRATEGY', text: 'Preset: Crypto Scalp (1M-5M Momentum)', action: 'preset', param: 'crypto_scalp' },
            { category: 'STRATEGY', text: 'Preset: Stock Swing (1H-1D Conviction)', action: 'preset', param: 'stock_swing' },
            { category: 'STRATEGY', text: 'Preset: Full Quant (All 10 Indicators)', action: 'preset', param: 'balanced' },
            // Overlays
            { category: 'OVERLAY', text: 'Toggle Level-2 Order Book (DOM Ladder)', action: 'toggle_dom', param: null },
            { category: 'OVERLAY', text: 'Toggle On-Chart TP / SL Price Lines', action: 'toggle_tpsl', param: null },
            { category: 'OVERLAY', text: 'Toggle On-Chart AI Predicted Target Price Line', action: 'toggle_ml_target', param: null },
            { category: 'OVERLAY', text: 'Toggle EMA Ribbons (20, 50, 200)', action: 'toggle_ema', param: null },
            { category: 'OVERLAY', text: 'Toggle Bollinger Bands Volatility Envelope', action: 'toggle_bb', param: null },
            { category: 'OVERLAY', text: 'Toggle On-Chart RSI Momentum Ribbon', action: 'toggle_rsi', param: null },
            { category: 'VIEW', text: 'Toggle Fullscreen Chart / Intel Sidebar', action: 'toggle_sidebar', param: null },
            // Paper Trading Commands
            { category: 'PAPER TRADE', text: 'Paper: Place Market Long (Current Symbol)', action: 'paper_long', param: null },
            { category: 'PAPER TRADE', text: 'Paper: Place Market Short (Current Symbol)', action: 'paper_short', param: null },
            { category: 'PAPER TRADE', text: 'Paper: Close All Open Positions', action: 'paper_close_all', param: null },
            { category: 'PAPER TRADE', text: 'Paper: Reset Virtual Balance ($100,000)', action: 'paper_reset', param: null },
            { category: 'PAPER TRADE', text: 'Paper: Export Trade Journal to CSV', action: 'paper_export', param: null },
            { category: 'PAPER TRADE', text: 'Paper: Focus Positions Tab', action: 'paper_tab', param: 'positions' },
            { category: 'PAPER TRADE', text: 'Paper: Focus Open Orders Tab', action: 'paper_tab', param: 'orders' },
            { category: 'PAPER TRADE', text: 'Paper: Focus Trade History Tab', action: 'paper_tab', param: 'history' },
            { category: 'PAPER TRADE', text: 'Paper: Focus Performance Analytics', action: 'paper_tab', param: 'analytics' },
            // Quant Auto-Pilot Bot Commands
            { category: 'BOT', text: 'Auto-Pilot: Toggle Autonomous Trading (ON/OFF)', action: 'ap_toggle', param: null },
            { category: 'BOT', text: 'Auto-Pilot: Set Conviction Threshold to 70%', action: 'ap_thresh', param: 0.70 },
            { category: 'BOT', text: 'Auto-Pilot: Set Conviction Threshold to 80%', action: 'ap_thresh', param: 0.80 },
            { category: 'BOT', text: 'Auto-Pilot: Emergency Stop (Disarm & Close All)', action: 'ap_kill', param: null },
            // News & Sentiment Commands
            { category: 'NEWS', text: 'News: Focus News & Sentiment Intelligence Hub', action: 'paper_tab', param: 'news' },
            // Backtest Studio Commands
            { category: 'BACKTEST', text: 'Backtest: Run Strategy Simulation (Current Asset)', action: 'run_backtest', param: null },
            { category: 'BACKTEST', text: 'Backtest: Focus Strategy Backtest Studio Tab', action: 'paper_tab', param: 'backtest' },
            // Market Regime Commands
            { category: 'REGIME', text: 'Market Regime: Inspect Macro Structure & Guardrails', action: 'inspect_regime', param: null },
            // Workspace Mode Commands
            { category: 'VIEW', text: 'Workspace: Terminal View (Chart + L2 DOM + Execution)', action: 'workspace_mode', param: 'terminal' },
            { category: 'VIEW', text: 'Workspace: Quant View (AI ML Forecast + Macro Regime)', action: 'workspace_mode', param: 'quant' },
            { category: 'VIEW', text: 'Workspace: Studio View (Strategy Backtester & News Hub)', action: 'workspace_mode', param: 'studio' }
        ];
    }

    renderCommandPalette(query) {
        if (!this.dom.cmdResultsList) return;
        const q = (query || '').trim().toLowerCase();
        const allCmds = this.getCommandList();
        const filtered = q ? allCmds.filter(c => c.text.toLowerCase().includes(q) || c.category.toLowerCase().includes(q)) : allCmds;

        let html = '';
        filtered.slice(0, 15).forEach(cmd => {
            html += `
                <div class="cmd-item" onclick="terminal.executeCommand('${cmd.action}', '${cmd.param}')">
                    <div class="cmd-item-left">
                        <span class="cmd-category-tag">${cmd.category}</span>
                        <span>${cmd.text}</span>
                    </div>
                    <span class="cmd-kbd">↵ Enter</span>
                </div>
            `;
        });
        if (filtered.length === 0) {
            html = `<div style="padding:16px; text-align:center; color:#536079; font-size:12px;">No matching command found for "${query}".</div>`;
        }
        this.dom.cmdResultsList.innerHTML = html;
    }

    executeCommand(action, param) {
        this.dom.cmdBackdrop.classList.add('hidden');
        if (action === 'symbol') {
            this.selectSymbol(param);
        } else if (action === 'tf') {
            this.setTimeframe(param);
            this.loadMarketData(true);
        } else if (action === 'model') {
            this.activeModel = param;
            if (this.dom.modelSwitch) {
                this.dom.modelSwitch.querySelectorAll('.model-toggle-btn').forEach(b => {
                    b.classList.toggle('active', b.dataset.model === param);
                });
            }
            this.loadMarketData(false);
        } else if (action === 'horizon') {
            this.predictionHorizon = parseInt(param, 10);
            if (this.dom.horizonChips) {
                this.dom.horizonChips.querySelectorAll('.horizon-chip').forEach(c => {
                    c.classList.toggle('active', parseInt(c.dataset.horizon, 10) === this.predictionHorizon);
                });
            }
            this.loadMarketData(false);
        } else if (action === 'preset') {
            this.activePreset = param;
            if (this.dom.headerPresetSelect) {
                this.dom.headerPresetSelect.value = param;
            }
            if (this.dom.presetChips) {
                this.dom.presetChips.querySelectorAll('.preset-chip').forEach(c => {
                    c.classList.toggle('active', c.dataset.preset === param);
                });
            }
            this.loadMarketData(true);
        } else if (action === 'toggle_tpsl') {
            this.showTpSl = !this.showTpSl;
            if (this.dom.btnToggleTpSl) this.dom.btnToggleTpSl.classList.toggle('active', this.showTpSl);
            this.updateTpSlPriceLines(this.cachedTargets);
        } else if (action === 'toggle_ml_target') {
            this.showMlTarget = !this.showMlTarget;
            if (this.dom.btnToggleMlTarget) this.dom.btnToggleMlTarget.classList.toggle('active', this.showMlTarget);
            this.updateMlTargetPriceLine(this.cachedMlPrediction, this.latestPrice);
        } else if (action === 'run_infer') {
            this.runQuickInference();
        } else if (action === 'toggle_ema') {
            this.showEma = !this.showEma;
            if (this.dom.btnToggleEma) this.dom.btnToggleEma.classList.toggle('active', this.showEma);
            if (this.ema20Series) this.ema20Series.applyOptions({ visible: this.showEma });
            if (this.ema50Series) this.ema50Series.applyOptions({ visible: this.showEma });
            if (this.ema200Series) this.ema200Series.applyOptions({ visible: this.showEma });
            if (this.showEma && this.cachedCandles) this.updateOverlaySeries(this.cachedCandles);
        } else if (action === 'toggle_bb') {
            this.showBb = !this.showBb;
            if (this.dom.btnToggleBb) this.dom.btnToggleBb.classList.toggle('active', this.showBb);
            if (this.bbUpperSeries) this.bbUpperSeries.applyOptions({ visible: this.showBb });
            if (this.bbLowerSeries) this.bbLowerSeries.applyOptions({ visible: this.showBb });
            if (this.showBb && this.cachedCandles) this.updateOverlaySeries(this.cachedCandles);
        } else if (action === 'toggle_dom') {
            if (this.wsManager) this.wsManager.toggleDom();
        } else if (action === 'toggle_rsi') {
            this.showRsi = !this.showRsi;
            if (this.dom.btnToggleRsi) this.dom.btnToggleRsi.classList.toggle('active', this.showRsi);
            this.updateRsiIndicator(this.cachedCandles);
        } else if (action === 'toggle_sidebar') {
            this.toggleSidebar();
        } else if (action === 'paper_long') {
            if (this.paper) {
                this.paper.selectedSide = 'LONG';
                this.paper.updateSideButtons();
                this.paper.executeOrder();
            }
        } else if (action === 'paper_short') {
            if (this.paper) {
                this.paper.selectedSide = 'SHORT';
                this.paper.updateSideButtons();
                this.paper.executeOrder();
            }
        } else if (action === 'paper_close_all') {
            if (this.paper) this.paper.closeAllPositions();
        } else if (action === 'paper_reset') {
            if (this.paper) this.paper.resetAccount();
        } else if (action === 'paper_export') {
            if (this.paper) this.paper.exportCSV();
        } else if (action === 'paper_tab') {
            if (this.paper) this.paper.switchTab(param);
        } else if (action === 'ap_toggle') {
            if (this.autoPilot) this.autoPilot.setEnabled(!this.autoPilot.enabled);
        } else if (action === 'ap_thresh') {
            if (this.autoPilot) {
                this.autoPilot.minConviction = param;
                this.autoPilot.setEnabled(true);
            }
        } else if (action === 'ap_kill') {
            if (this.autoPilot) this.autoPilot.emergencyStop();
        } else if (action === 'run_backtest') {
            if (this.paper) this.paper.switchTab('backtest');
            this.loadBacktestData(true);
        } else if (action === 'inspect_regime') {
            if (this.cachedRegime && this.paper) {
                const r = this.cachedRegime;
                const m = r.metrics || {};
                this.paper.showToast('info', `📊 ${r.label}`, `${r.description} (ADX: ${m.adx || 'N/A'}, ATR Exp: ${m.atr_expansion || 'N/A'}x). Strategy: ${r.strategy_bias}`);
            }
        } else if (action === 'workspace_mode') {
            this.setWorkspaceMode(param);
        }
    }
}

// =========================================================================
// Quant Auto-Pilot: Autonomous Algorithmic Trading Bot
// =========================================================================

class QuantAutoPilot {
    constructor(terminal, paper) {
        this.terminal = terminal;
        this.paper = paper;
        this.enabled = false;

        // Configurable risk parameters
        this.minConviction = 0.70; // 70% confidence threshold default
        this.allocationPct = 0.10; // 10% of available margin per trade
        this.leverage = 5;
        this.maxPositions = 3;
        this.maxDailyDrawdownPct = 3.0; // 3% circuit breaker
        
        // Cooldown and rate-limiting
        this.lastOrderTimeBySymbol = {};
        this.startDayEquity = (this.paper && this.paper.balance) ? this.paper.balance : 100000;
        this.autoTradesCount = 0;
        this.aiFilterEnabled = true;

        this.dom = {
            toggle: document.getElementById('toggle-autopilot'),
            statusTag: document.getElementById('ap-status-tag'),
            box: document.getElementById('auto-pilot-box'),
            guardrails: document.getElementById('ap-guardrails-panel'),
            dockBadge: document.getElementById('dock-ap-status'),
            thresholdChips: document.getElementById('ap-threshold-chips'),
            allocChips: document.getElementById('ap-alloc-chips'),
            toggleAiFilter: document.getElementById('toggle-ap-ml-filter'),
            aiFilterStatus: document.getElementById('ap-ml-filter-status'),
            killBtn: document.getElementById('btn-ap-kill')
        };

        this.initEvents();
    }

    initEvents() {
        if (this.dom.toggle) {
            this.dom.toggle.addEventListener('change', (e) => {
                this.setEnabled(e.target.checked);
            });
        }

        if (this.dom.toggleAiFilter) {
            this.dom.toggleAiFilter.addEventListener('change', (e) => {
                this.aiFilterEnabled = e.target.checked;
                if (this.dom.aiFilterStatus) {
                    this.dom.aiFilterStatus.textContent = this.aiFilterEnabled ? 'ENFORCED' : 'OFF';
                    this.dom.aiFilterStatus.className = `ap-filter-status ${this.aiFilterEnabled ? '' : 'off'}`;
                }
            });
        }

        if (this.dom.thresholdChips) {
            this.dom.thresholdChips.addEventListener('click', (e) => {
                const btn = e.target.closest('.ap-chip');
                if (!btn) return;
                this.dom.thresholdChips.querySelectorAll('.ap-chip').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.minConviction = parseFloat(btn.dataset.val);
            });
        }

        if (this.dom.allocChips) {
            this.dom.allocChips.addEventListener('click', (e) => {
                const btn = e.target.closest('.ap-chip');
                if (!btn) return;
                this.dom.allocChips.querySelectorAll('.ap-chip').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.allocationPct = parseFloat(btn.dataset.val);
            });
        }

        if (this.dom.killBtn) {
            this.dom.killBtn.addEventListener('click', () => {
                this.emergencyStop();
            });
        }
    }

    setEnabled(val) {
        this.enabled = val;
        if (this.dom.box) {
            if (this.enabled) this.dom.box.classList.add('engaged');
            else this.dom.box.classList.remove('engaged');
        }
        if (this.dom.guardrails) {
            if (this.enabled) this.dom.guardrails.classList.remove('hidden');
            else this.dom.guardrails.classList.add('hidden');
        }
        if (this.dom.statusTag) {
            this.dom.statusTag.textContent = this.enabled ? '🟢 ENGAGED' : 'DISARMED';
            this.dom.statusTag.className = `ap-status-tag ${this.enabled ? 'active' : ''}`;
        }
        if (this.dom.dockBadge) {
            this.dom.dockBadge.textContent = this.enabled ? 'ARMED' : 'OFF';
            this.dom.dockBadge.className = `pill-val ${this.enabled ? 'active' : 'neutral'}`;
        }

        if (this.enabled) {
            this.paper.showToast('fill', '🤖 Auto-Pilot Armed', `Monitoring signals with ≥${Math.round(this.minConviction*100)}% conviction threshold.`);
        } else {
            this.paper.showToast('info', '🤖 Auto-Pilot Disarmed', 'Manual trading mode active.');
        }
    }

    emergencyStop() {
        this.setEnabled(false);
        if (this.dom.toggle) this.dom.toggle.checked = false;
        this.paper.closeAllPositions();
        this.paper.showToast('sl', '🛑 EMERGENCY ALL-STOP', 'Auto-Pilot disarmed and all open positions market-closed.');
    }

    evaluateSignal(symbol, curPrice, signalObj, targets, regime, mlPrediction) {
        if (!this.enabled || !signalObj || !curPrice || curPrice <= 0) return;

        const sig = signalObj.signal;
        const strength = signalObj.strength || 0;

        // 1. Only execute high-conviction BUY or SELL
        if (sig !== 'BUY' && sig !== 'SELL') return;

        // 1b. Check Institutional Market Regime Guardrails
        const currentRegime = regime || (this.terminal ? this.terminal.cachedRegime : null);
        if (currentRegime) {
            const rType = currentRegime.regime;
            // Guardrail 1: Volatility Hazard -> Block automated trading completely
            if (rType === 'VOLATILITY_HAZARD' || (currentRegime.rules && currentRegime.rules.allow_auto_pilot === false)) {
                return;
            }
            // Guardrail 2: Trending Bull -> No counter-trend shorting allowed
            if (rType === 'TRENDING_BULL' && sig === 'SELL') {
                return;
            }
            // Guardrail 3: Trending Bear -> No counter-trend dip buying allowed
            if (rType === 'TRENDING_BEAR' && sig === 'BUY') {
                return;
            }
            // Guardrail 4: Choppy Range -> Enforce higher minimum conviction threshold (≥80%)
            if (rType === 'CHOPPY_RANGE') {
                const chopThreshold = Math.max(this.minConviction, 0.80);
                if (strength < chopThreshold) return;
            }
        }

        // 1c. Machine Learning / AI Directional Consensus Check
        if (this.aiFilterEnabled && mlPrediction) {
            const mlDir = (mlPrediction.direction || '').toUpperCase();
            const mlConf = mlPrediction.confidence || 0.5;

            // Reject trades that directly oppose high-conviction AI forecast
            if (sig === 'BUY' && mlDir === 'BEARISH' && mlConf >= 0.42) {
                console.log(`[AutoPilot] Blocked BUY on ${symbol}: AI Predictor is BEARISH (${Math.round(mlConf*100)}%)`);
                return;
            }
            if (sig === 'SELL' && mlDir === 'BULLISH' && mlConf >= 0.42) {
                console.log(`[AutoPilot] Blocked SELL on ${symbol}: AI Predictor is BULLISH (${Math.round(mlConf*100)}%)`);
                return;
            }
        }

        if (strength < this.minConviction) return;

        // 2. Check Cooldown (at least 45 seconds between automated entries on the same symbol)
        const now = Date.now();
        const lastTime = this.lastOrderTimeBySymbol[symbol] || 0;
        if (now - lastTime < 45000) return;

        // 3. Check Risk Guardrail: Daily Drawdown Circuit Breaker
        const currentEquity = this.paper.balance + this.paper.positions.reduce((acc, p) => acc + (p.margin + p.unrealizedPnl), 0);
        const drawdownPct = ((this.startDayEquity - currentEquity) / this.startDayEquity) * 100;
        if (drawdownPct >= this.maxDailyDrawdownPct) {
            this.paper.showToast('sl', '🛡️ Circuit Breaker Tripped', `Daily drawdown (-${drawdownPct.toFixed(1)}%) breached -3.0% limit. Auto-Pilot paused.`);
            this.setEnabled(false);
            if (this.dom.toggle) this.dom.toggle.checked = false;
            return;
        }

        // 4. Check Risk Guardrail: Max Concurrent Positions & Existing Asset
        const existingPos = this.paper.positions.find(p => p.symbol === symbol);
        const targetSide = sig === 'BUY' ? 'LONG' : 'SHORT';

        if (existingPos) {
            // Already long on buy or short on sell -> skip duplicate order
            if (existingPos.side === targetSide) return;
            // Opposite direction -> smart reversal
            this.paper.reversePosition(existingPos.id);
            this.lastOrderTimeBySymbol[symbol] = now;
            this.autoTradesCount++;
            this.paper.showToast('fill', `🤖 Auto-Pilot Reversal`, `Flipped ${symbol.replace('-USD','')} to ${targetSide} on ${Math.round(strength*100)}% conviction.`);
            return;
        }

        if (this.paper.positions.length >= this.maxPositions) {
            return; // At max capacity
        }

        // 5. Margin allocation check
        const availMargin = this.paper.calcAvailableMargin();
        const orderMargin = Math.max(100, Math.min(availMargin, this.paper.balance * this.allocationPct));
        if (orderMargin > availMargin || orderMargin < 100) return;

        // 6. Dynamic ATR TP / SL
        let tp = targets ? targets.tp : null;
        let sl = targets ? targets.sl : null;
        if (!tp || !sl) {
            const atr = targets ? targets.atr : curPrice * 0.02;
            tp = targetSide === 'LONG' ? (curPrice + 2 * atr) : (curPrice - 2 * atr);
            sl = targetSide === 'LONG' ? (curPrice - 1.5 * atr) : (curPrice + 1.5 * atr);
        }

        // 7. Execute Autonomous Order
        const notional = orderMargin * this.leverage;
        const qty = notional / curPrice;
        const fee = notional * 0.0004;
        this.paper.balance -= (orderMargin + fee);

        const newPos = {
            id: 'AP-' + Math.random().toString(36).substring(2, 8).toUpperCase(),
            symbol: symbol,
            side: targetSide,
            qty: qty,
            entryPrice: curPrice,
            markPrice: curPrice,
            margin: orderMargin,
            leverage: this.leverage,
            notional: notional,
            liqPrice: this.paper.calcLiqPrice(targetSide, curPrice, this.leverage),
            tp: tp,
            sl: sl,
            unrealizedPnl: 0,
            unrealizedPnlPct: 0,
            openTime: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            isAutoPilot: true
        };

        this.paper.positions.push(newPos);
        this.lastOrderTimeBySymbol[symbol] = now;
        this.autoTradesCount++;
        this.paper.saveState();
        this.paper.updateUI();
        this.paper.updateChartPositionLines();

        if (this.terminal.wsManager) {
            this.terminal.wsManager.playTradeChirp(targetSide === 'LONG', qty);
        }

        this.paper.showToast('fill', `🤖 Auto-Pilot Executed`, `${targetSide} ${qty < 1 ? qty.toFixed(4) : qty.toFixed(2)} ${symbol.replace('-USD','')} @ $${curPrice > 10 ? curPrice.toLocaleString(undefined, {minimumFractionDigits: 2}) : curPrice.toFixed(4)} (${Math.round(strength*100)}% Conf.)`);
    }
}

// =========================================================================
// Real-Time 0-Latency Binance Public WebSocket Streaming Manager
// =========================================================================

class BinanceWebSocketManager {
    constructor(terminal) {
        this.terminal = terminal;
        this.ws = null;
        this.reconnectTimer = null;
        this.lastPrice = 0;
        this.isCrypto = true;

        this.cryptoSymbols = [
            'BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'DOGE-USD', 'ADA-USD', 'BNB-USD'
        ];

        this.dom = {
            badge: document.getElementById('ws-status-badge'),
            statusText: document.getElementById('ws-status-text'),
            tapeText: document.getElementById('trade-tape-text'),
            tapeDot: document.getElementById('trade-side-dot'),
            speedBadge: document.getElementById('trade-speed-badge'),
            audioBtn: document.getElementById('btn-toggle-audio'),
            audioDot: document.getElementById('audio-dot'),
            domPanel: document.getElementById('dom-ladder-panel'),
            domBtn: document.getElementById('btn-toggle-dom'),
            domAsksList: document.getElementById('dom-asks-list'),
            domBidsList: document.getElementById('dom-bids-list'),
            domMidPrice: document.getElementById('dom-mid-price'),
            domMidSpread: document.getElementById('dom-mid-spread'),
            domSpreadBadge: document.getElementById('dom-spread-badge'),
            domBidsPct: document.getElementById('dom-bids-pct'),
            domAsksPct: document.getElementById('dom-asks-pct'),
            domImbalanceBids: document.getElementById('dom-imbalance-bids'),
            domImbalanceAsks: document.getElementById('dom-imbalance-asks')
        };

        this.txCount = 0;
        this.txRate = 0;
        this.audioEnabled = false;
        this.audioCtx = null;

        if (this.dom.audioBtn) {
            this.dom.audioBtn.addEventListener('click', () => this.toggleAudio());
        }

        if (this.dom.domBtn) {
            this.dom.domBtn.addEventListener('click', () => this.toggleDom());
        }

        setInterval(() => this.updateSpeedometer(), 1000);
    }

    toggleDom() {
        if (!this.dom.domPanel) return;
        const isHidden = this.dom.domPanel.classList.toggle('hidden');
        if (this.dom.domBtn) {
            this.dom.domBtn.classList.toggle('active', !isHidden);
        }
        setTimeout(() => {
            if (this.terminal && this.terminal.chart) {
                this.terminal.resizeChart();
            }
        }, 50);
    }

    toggleAudio() {
        this.audioEnabled = !this.audioEnabled;
        if (this.audioEnabled && !this.audioCtx) {
            try {
                const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
                if (AudioCtxClass) this.audioCtx = new AudioCtxClass();
            } catch (e) {}
        }
        if (this.audioCtx && this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }
        if (this.dom.audioBtn) {
            this.dom.audioBtn.innerHTML = `<span class="btn-dot ${this.audioEnabled ? 'active-audio' : 'gray'}" id="audio-dot"></span> ${this.audioEnabled ? '🔊 Audio ON' : '🔈 Audio Tape'}`;
        }
    }

    playTradeChirp(isBuy, qty) {
        if (!this.audioEnabled || !this.audioCtx) return;
        try {
            const osc = this.audioCtx.createOscillator();
            const gain = this.audioCtx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(isBuy ? 880 : 520, this.audioCtx.currentTime);
            const vol = Math.min(0.035, Math.max(0.008, 0.01 + (qty * 0.005)));
            gain.gain.setValueAtTime(vol, this.audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, this.audioCtx.currentTime + 0.025);
            osc.connect(gain);
            gain.connect(this.audioCtx.destination);
            osc.start();
            osc.stop(this.audioCtx.currentTime + 0.025);
        } catch (e) {}
    }

    playSuccessChime() {
        if (!this.audioCtx) {
            try {
                const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
                if (AudioCtxClass) this.audioCtx = new AudioCtxClass();
            } catch (e) {}
        }
        if (!this.audioCtx) return;
        try {
            const now = this.audioCtx.currentTime;
            [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
                const osc = this.audioCtx.createOscillator();
                const gain = this.audioCtx.createGain();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(freq, now + (i * 0.08));
                gain.gain.setValueAtTime(0.08, now + (i * 0.08));
                gain.gain.exponentialRampToValueAtTime(0.0001, now + (i * 0.08) + 0.2);
                osc.connect(gain);
                gain.connect(this.audioCtx.destination);
                osc.start(now + (i * 0.08));
                osc.stop(now + (i * 0.08) + 0.2);
            });
        } catch (e) {}
    }

    updateSpeedometer() {
        this.txRate = this.txCount;
        this.txCount = 0;
        if (this.dom.speedBadge) {
            this.dom.speedBadge.textContent = `${this.txRate} tx/s`;
        }
        if (this.dom.badge && this.isCrypto && this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.dom.statusText.textContent = `LIVE 0ms WS (${this.txRate} tx/s)`;
        }
    }

    toBinanceSymbol(sym) {
        if (!sym) return null;
        const clean = sym.toUpperCase().replace('-USD', '').replace('USDT', '');
        const cryptoMap = {
            'BTC': 'btcusdt',
            'ETH': 'ethusdt',
            'SOL': 'solusdt',
            'XRP': 'xrpusdt',
            'DOGE': 'dogeusdt',
            'ADA': 'adausdt',
            'BNB': 'bnbusdt',
            'AVAX': 'avaxusdt',
            'DOT': 'dotusdt',
            'MATIC': 'maticusdt',
            'LINK': 'linkusdt',
            'NEAR': 'nearusdt'
        };
        return cryptoMap[clean] || (sym.endsWith('-USD') ? `${clean.toLowerCase()}usdt` : null);
    }

    toBinanceInterval(tf) {
        const map = {
            '1m': '1m',
            '3m': '3m',
            '5m': '5m',
            '15m': '15m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d'
        };
        return map[tf] || '1h';
    }

    connect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        const activeBinanceSym = this.toBinanceSymbol(this.terminal.activeSymbol);
        this.isCrypto = Boolean(activeBinanceSym);

        if (!this.isCrypto) {
            this.setStatus('rest', 'REST (NSE 15M)');
            if (this.dom.tapeText) this.dom.tapeText.textContent = 'REST FEED';
            if (this.dom.speedBadge) this.dom.speedBadge.textContent = 'REST';
            if (this.ws) {
                try { this.ws.close(); } catch(e) {}
                this.ws = null;
            }
            return;
        }

        // Combine watchlist tickers + active symbol kline candle stream + active aggTrade millisecond stream
        const tickerStreams = this.cryptoSymbols
            .map(s => this.toBinanceSymbol(s))
            .filter(Boolean)
            .map(s => `${s}@ticker`);

        const klineStream = `${activeBinanceSym}@kline_${this.toBinanceInterval(this.terminal.activeTimeframe)}`;
        const aggTradeStream = `${activeBinanceSym}@aggTrade`;
        const depthStream = `${activeBinanceSym}@depth10@100ms`;
        const streamList = Array.from(new Set([...tickerStreams, klineStream, aggTradeStream, depthStream]));
        const wsUrl = `wss://stream.binance.com:9443/stream?streams=${streamList.join('/')}`;

        this.setStatus('rest', 'WS CONNECTING...');

        try {
            if (this.ws) {
                this.ws.onclose = null;
                this.ws.onerror = null;
                this.ws.close();
            }

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                this.setStatus('live', 'LIVE 0ms WS');
            };

            this.ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    this.handleMessage(msg);
                } catch (e) {
                    console.error("WS Parse error:", e);
                }
            };

            this.ws.onerror = () => {
                this.setStatus('rest', 'WS RETRYING...');
            };

            this.ws.onclose = () => {
                if (this.isCrypto) {
                    this.setStatus('rest', 'WS DISCONNECTED');
                    this.reconnectTimer = setTimeout(() => this.connect(), 3000);
                }
            };

        } catch (e) {
            console.error("WebSocket init failed:", e);
            this.setStatus('rest', 'WS OFFLINE');
        }
    }

    handleMessage(msg) {
        if (!msg || !msg.data) return;
        const data = msg.data;
        const stream = msg.stream || '';

        if (stream.endsWith('@aggTrade')) {
            this.handleAggTrade(data);
        } else if (stream.endsWith('@ticker')) {
            this.handleTicker(data);
        } else if (stream.includes('@kline')) {
            this.handleKline(data);
        } else if (stream.includes('@depth')) {
            this.handleDepth(data);
        }
    }

    handleDepth(data) {
        if (!data || !data.bids || !data.asks) return;
        if (!this.dom.domPanel || this.dom.domPanel.classList.contains('hidden')) return;

        const rawAsks = data.asks.slice(0, 6);
        const rawBids = data.bids.slice(0, 6);

        // Cumulative asks calculations
        let cumAsk = 0;
        const asksWithCum = rawAsks.map(([p, q]) => {
            const price = parseFloat(p);
            const qty = parseFloat(q);
            cumAsk += qty;
            return { price, qty, cum: cumAsk };
        });

        // Cumulative bids calculations
        let cumBid = 0;
        const bidsWithCum = rawBids.map(([p, q]) => {
            const price = parseFloat(p);
            const qty = parseFloat(q);
            cumBid += qty;
            return { price, qty, cum: cumBid };
        });

        const maxTotal = Math.max(cumAsk, cumBid, 0.0001);

        // Order flow imbalance over all 10 depth levels
        const allAsksSum = data.asks.reduce((acc, a) => acc + parseFloat(a[1]), 0);
        const allBidsSum = data.bids.reduce((acc, b) => acc + parseFloat(b[1]), 0);
        const totalVol = (allBidsSum + allAsksSum) || 1;
        const bidsPct = Math.round((allBidsSum / totalVol) * 100);
        const asksPct = 100 - bidsPct;

        if (this.dom.domBidsPct) this.dom.domBidsPct.textContent = `${bidsPct}% Bids`;
        if (this.dom.domAsksPct) this.dom.domAsksPct.textContent = `${asksPct}% Asks`;
        if (this.dom.domImbalanceBids) this.dom.domImbalanceBids.style.width = `${bidsPct}%`;
        if (this.dom.domImbalanceAsks) this.dom.domImbalanceAsks.style.width = `${asksPct}%`;

        // Mid-market mark price and spread
        const bestBid = parseFloat(data.bids[0][0]);
        const bestAsk = parseFloat(data.asks[0][0]);
        const midPrice = (bestBid + bestAsk) / 2;
        const spread = bestAsk - bestBid;
        const spreadPct = (spread / midPrice) * 100;

        if (this.dom.domSpreadBadge) {
            this.dom.domSpreadBadge.textContent = `Spread: $${spread < 0.01 ? spread.toFixed(4) : spread.toFixed(2)}`;
        }
        if (this.dom.domMidPrice) {
            this.dom.domMidPrice.textContent = `$${midPrice > 10 ? midPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : midPrice.toFixed(4)}`;
        }
        if (this.dom.domMidSpread) {
            this.dom.domMidSpread.textContent = `${spreadPct.toFixed(3)}%`;
        }

        const fmtPrice = p => p > 10 ? p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : p.toFixed(4);
        const fmtQty = q => q < 1 ? q.toFixed(4) : (q < 100 ? q.toFixed(2) : Math.round(q).toLocaleString());

        // Render Asks (descending so closest ask to mid is at bottom)
        if (this.dom.domAsksList) {
            const reversedAsks = [...asksWithCum].reverse();
            this.dom.domAsksList.innerHTML = reversedAsks.map(item => {
                const depthPct = Math.min(100, Math.round((item.cum / maxTotal) * 100));
                return `<div class="dom-row ask" onclick="window.terminal.copyDomPrice(${item.price}, 'SELL')" title="Click to Stage Limit Sell at $${fmtPrice(item.price)}">
                    <div class="dom-depth-bar" style="width: ${depthPct}%"></div>
                    <span>${fmtPrice(item.price)}</span>
                    <span>${fmtQty(item.qty)}</span>
                    <span>${fmtQty(item.cum)}</span>
                </div>`;
            }).join('');
        }

        // Render Bids (highest bid closest to mid at top)
        if (this.dom.domBidsList) {
            this.dom.domBidsList.innerHTML = bidsWithCum.map(item => {
                const depthPct = Math.min(100, Math.round((item.cum / maxTotal) * 100));
                return `<div class="dom-row bid" onclick="window.terminal.copyDomPrice(${item.price}, 'BUY')" title="Click to Stage Limit Buy at $${fmtPrice(item.price)}">
                    <div class="dom-depth-bar" style="width: ${depthPct}%"></div>
                    <span>${fmtPrice(item.price)}</span>
                    <span>${fmtQty(item.qty)}</span>
                    <span>${fmtQty(item.cum)}</span>
                </div>`;
            }).join('');
        }
    }

    handleAggTrade(data) {
        // data.p = execution price, data.q = quantity, data.m = buyer is maker (true = sell, false = buy)
        const price = parseFloat(data.p);
        const isBuyerMaker = data.m;
        const isBuy = !isBuyerMaker;
        const qty = parseFloat(data.q);
        const fullSymbol = data.s.replace('USDT', '-USD');

        this.txCount++;

        if (this.terminal.activeSymbol === fullSymbol) {
            // Update millisecond trade flow HUD
            if (this.dom.tapeText) {
                const sideStr = isBuy ? '▲ BUY' : '▼ SELL';
                const cleanSym = fullSymbol.replace('-USD', '');
                const qtyStr = qty < 1 ? qty.toFixed(4) : (qty < 10 ? qty.toFixed(2) : Math.round(qty));
                const priceStr = price > 10 ? price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : price.toFixed(4);
                this.dom.tapeText.textContent = `${sideStr} ${qtyStr} ${cleanSym} @ $${priceStr}`;
                this.dom.tapeText.className = `trade-tape-text ${isBuy ? 'flash-buy' : 'flash-sell'}`;

                if (this.dom.tapeDot) {
                    this.dom.tapeDot.className = `trade-side-dot ${isBuy ? 'buy' : 'sell'}`;
                }
            }

            if (this.audioEnabled) {
                this.playTradeChirp(isBuy, qty);
            }

            // Immediate millisecond visual price update with green/red flash
            this.updateActivePrice(price, isBuy);

            // Dynamically update the current live candlestick at 60 FPS
            if (this.terminal.candlestickSeries && this.lastCandle) {
                this.lastCandle.close = price;
                if (price > this.lastCandle.high) this.lastCandle.high = price;
                if (price < this.lastCandle.low) this.lastCandle.low = price;
                this.terminal.candlestickSeries.update(this.lastCandle);
            }

            // Real-time sub-second Paper Trading tick execution
            if (this.terminal.paper) {
                this.terminal.paper.onPriceTick(fullSymbol, price);
            }
        }
    }

    handleTicker(data) {
        const sym = data.s; // e.g. "BTCUSDT"
        const price = parseFloat(data.c);
        const changePct = parseFloat(data.P);
        const fullSymbol = sym.replace('USDT', '-USD');

        // Update top ticker banner item in real time
        const tickerItem = document.querySelector(`.ticker-item[onclick*="${fullSymbol}"]`);
        if (tickerItem) {
            const priceEl = tickerItem.querySelector('.ticker-price');
            const chgEl = tickerItem.querySelector('.ticker-chg');
            if (priceEl) priceEl.textContent = `$${price > 10 ? price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : price.toFixed(4)}`;
            if (chgEl) {
                const isPos = changePct >= 0;
                chgEl.textContent = `${isPos ? '+' : ''}${changePct.toFixed(2)}%`;
                chgEl.className = `ticker-chg ${isPos ? 'pos' : 'neg'}`;
            }
        }

        // Notify Paper Trading Engine of tick across all open positions
        if (this.terminal.paper) {
            this.terminal.paper.onPriceTick(fullSymbol, price);
        }

        // If ticker matches currently viewed symbol
        if (this.terminal.activeSymbol === fullSymbol) {
            this.updateActivePrice(price);
        }
    }

    handleKline(data) {
        if (!data || !data.k) return;
        const k = data.k;
        const curPrice = parseFloat(k.c);
        const fullSymbol = data.s.replace('USDT', '-USD');

        if (this.terminal.activeSymbol === fullSymbol) {
            this.updateActivePrice(curPrice);

            // Update live pulsing candle on TradingView 60 FPS canvas
            if (this.terminal.candlestickSeries) {
                const candleTime = Math.floor(k.t / 1000);
                this.terminal.candlestickSeries.update({
                    time: candleTime,
                    open: parseFloat(k.o),
                    high: parseFloat(k.h),
                    low: parseFloat(k.l),
                    close: curPrice
                });
            }

            // Real-time paper trading update
            if (this.terminal.paper) {
                this.terminal.paper.onPriceTick(fullSymbol, curPrice);
            }
        }
    }

    updateActivePrice(curPrice, isBuy = null) {
        const displayEl = this.terminal.dom.displayPrice;
        if (!displayEl) return;

        const prevPrice = this.lastPrice || this.terminal.latestPrice;
        this.lastPrice = curPrice;
        this.terminal.latestPrice = curPrice;

        displayEl.textContent = `$${curPrice > 10 ? curPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : curPrice.toFixed(4)}`;

        let flashClass = null;
        if (isBuy !== null) {
            flashClass = isBuy ? 'price-flash-up' : 'price-flash-down';
        } else if (prevPrice && prevPrice !== curPrice) {
            flashClass = curPrice > prevPrice ? 'price-flash-up' : 'price-flash-down';
        }

        if (flashClass) {
            displayEl.classList.remove('price-flash-up', 'price-flash-down');
            void displayEl.offsetWidth; // Force CSS reflow
            displayEl.classList.add(flashClass);
        }
    }

    updateActiveSymbol(symbol) {
        const activeBinanceSym = this.toBinanceSymbol(symbol);
        this.isCrypto = Boolean(activeBinanceSym);
        this.lastPrice = 0;
        this.connect();
    }

    updateActiveTimeframe(tf) {
        if (this.isCrypto) {
            this.connect();
        }
    }

    setStatus(type, text) {
        if (!this.dom.badge || !this.dom.statusText) return;
        this.dom.badge.className = `ws-status-badge ${type}`;
        this.dom.statusText.textContent = text;
    }
}

// Global instance initialization on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    window.terminal = new TradeSignalTerminal();
});
