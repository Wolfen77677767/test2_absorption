/* ================================================
   SETTINGS PANEL v6 — Robuste & Complet
   ================================================ */
(function(){
'use strict';

/* ---- Helpers ---- */
const qs = id => document.getElementById(id);
const qsa = sel => document.querySelectorAll(sel);

/* ---- Config ---- */
const KEY = 'app-ui-settings';
const DEF = {
    theme:'dark-mode', primaryColor:'#0066FF',
    fontFamily:'Segoe UI', fontFallback:'Tahoma, Geneva, Verdana, sans-serif',
    fontSize:15, fontWeight:'normal', letterSpacing:0, lineHeight:1.6,
    background:'bg-none', sidebarCompact:false, animations:true,
    customBgGradient:null, customBgName:null
};

/* ---- Data ---- */
const THEMES = [
    /* Sombres */
    {id:'dark-mode',    label:'🌑 Sombre',     top:'#0a0e27', bot:'#1a1f3a'},
    {id:'theme-slate',  label:'🪨 Ardoise',    top:'#0f172a', bot:'#1e293b'},
    {id:'theme-ocean',  label:'🌊 Océan',      top:'#0b1d2e', bot:'#12344d'},
    {id:'theme-teal',   label:'🐢 Turquoise',  top:'#042f2e', bot:'#134e4a'},
    {id:'theme-forest', label:'🌿 Forêt',      top:'#1a2e1a', bot:'#0d1f0d'},
    {id:'theme-purple', label:'💜 Violet',     top:'#1e0b2e', bot:'#2e1a4a'},
    {id:'theme-rose',   label:'🌸 Rose',       top:'#2e0b1a', bot:'#4a1a2e'},
    {id:'theme-sunset', label:'🌅 Coucher',    top:'#2e1a0e', bot:'#1f0d05'},
    {id:'theme-amber',  label:'🌙 Doré',       top:'#1c1400', bot:'#3d2e00'},
    /* Clairs */
    {id:'light-mode',   label:'☀️ Blanc',      top:'#f8fafc', bot:'#ffffff'},
    {id:'theme-mint',   label:'🌱 Menthe',     top:'#ecfdf5', bot:'#d1fae5'},
    {id:'theme-sky',    label:'☁️ Ciel',       top:'#f0f9ff', bot:'#e0f2fe'},
    {id:'theme-peach',  label:'🍑 Pêche',      top:'#fff7ed', bot:'#fed7aa'},
    {id:'theme-lavender',label:'💐 Lavande',   top:'#faf5ff', bot:'#ede9fe'},
    /* Neons */
    {id:'theme-cyber',  label:'⚡ Cyber',      top:'#0d0221', bot:'#190a4e'},
    {id:'theme-matrix', label:'💚 Matrix',     top:'#001100', bot:'#003300'},
    {id:'theme-neon',   label:'🔴 Neon',       top:'#0a0000', bot:'#2a0000'},
];
const COLORS = [
    /* Row 1 — Blues & Cyans */
    {c:'#0066FF',l:'Bleu'},      {c:'#3b82f6',l:'Bleu clair'},  {c:'#00D9FF',l:'Cyan'},
    {c:'#06b6d4',l:'Azur'},      {c:'#0284c7',l:'Bleu roi'},    {c:'#1d4ed8',l:'Marine'},
    /* Row 2 — Greens */
    {c:'#10b981',l:'Vert'},      {c:'#22c55e',l:'Lime'},        {c:'#14b8a6',l:'Teal'},
    {c:'#16a34a',l:'Forêt'},     {c:'#84cc16',l:'Chartreuse'},  {c:'#059669',l:'Émeraude'},
    /* Row 3 — Warm */
    {c:'#f59e0b',l:'Orange'},    {c:'#f97316',l:'Mandarine'},   {c:'#ef4444',l:'Rouge'},
    {c:'#dc2626',l:'Carmin'},    {c:'#e11d48',l:'Framboise'},   {c:'#fbbf24',l:'Jaune'},
    /* Row 4 — Purples & Pinks */
    {c:'#8b5cf6',l:'Violet'},    {c:'#a855f7',l:'Mauve'},       {c:'#ec4899',l:'Rose'},
    {c:'#d946ef',l:'Fuchsia'},   {c:'#7c3aed',l:'Indigo'},      {c:'#be185d',l:'Pivoine'},
    /* Row 5 — Neutrals */
    {c:'#64748b',l:'Gris bleu'}, {c:'#6b7280',l:'Gris'},        {c:'#0f766e',l:'Pétrole'},
    {c:'#b45309',l:'Bronze'},    {c:'#ffffff',l:'Blanc'},        {c:'#f0abfc',l:'Lilas'},
];
const FONTS = [
    /* === Sans-serif === */
    {k:'Segoe UI',           l:'Segoe UI',        g:false, cat:'Sans'},
    {k:'Arial',              l:'Arial',            g:false, cat:'Sans'},
    {k:'Calibri',            l:'Calibri',          g:false, cat:'Sans'},
    {k:'Verdana',            l:'Verdana',          g:false, cat:'Sans'},
    {k:'Tahoma',             l:'Tahoma',           g:false, cat:'Sans'},
    {k:'Trebuchet MS',       l:'Trebuchet MS',     g:false, cat:'Sans'},
    {k:'Century Gothic',     l:'Century Gothic',   g:false, cat:'Sans'},
    {k:'Gill Sans MT',       l:'Gill Sans',        g:false, cat:'Sans'},
    /* === Serif === */
    {k:'Georgia',            l:'Georgia',          g:false, cat:'Serif'},
    {k:'Palatino Linotype',  l:'Palatino',         g:false, cat:'Serif'},
    {k:'Times New Roman',    l:'Times New Roman',  g:false, cat:'Serif'},
    {k:'Garamond',           l:'Garamond',         g:false, cat:'Serif'},
    {k:'Book Antiqua',       l:'Book Antiqua',     g:false, cat:'Serif'},
    {k:'Cambria',            l:'Cambria',          g:false, cat:'Serif'},
    /* === Monospace === */
    {k:'Courier New',        l:'Courier New',      g:false, cat:'Mono'},
    {k:'Consolas',           l:'Consolas',         g:false, cat:'Mono'},
    {k:'Lucida Console',     l:'Lucida Console',   g:false, cat:'Mono'},
    /* === Stylisées === */
    {k:'Impact',             l:'Impact',           g:false, cat:'Style'},
    {k:'Comic Sans MS',      l:'Comic Sans',       g:false, cat:'Style'},
    {k:'Copperplate Gothic', l:'Copperplate',      g:false, cat:'Style'},
    /* === Google Fonts (chargées dynamiquement) === */
    {k:'Roboto',             l:'Roboto',           g:true,  cat:'Google'},
    {k:'Open Sans',          l:'Open Sans',        g:true,  cat:'Google'},
    {k:'Lato',               l:'Lato',             g:true,  cat:'Google'},
    {k:'Montserrat',         l:'Montserrat',       g:true,  cat:'Google'},
    {k:'Poppins',            l:'Poppins',          g:true,  cat:'Google'},
    {k:'Raleway',            l:'Raleway',          g:true,  cat:'Google'},
    {k:'Nunito',             l:'Nunito',           g:true,  cat:'Google'},
    {k:'Playfair Display',   l:'Playfair Display', g:true,  cat:'Google'},
    {k:'Merriweather',       l:'Merriweather',     g:true,  cat:'Google'},
    {k:'Source Code Pro',    l:'Source Code Pro',  g:true,  cat:'Google'},
    {k:'Ubuntu',             l:'Ubuntu',           g:true,  cat:'Google'},
    {k:'Oswald',             l:'Oswald',           g:true,  cat:'Google'},
];
const BGS = [
    {id:'bg-none',    g:'',                                                              l:'Aucun'},
    /* Nuits & Espaces */
    {id:'bg-grad-1',  g:'linear-gradient(135deg,#0a0e27,#1a2a4a)',                      l:'Nuit bleue'},
    {id:'bg-grad-10', g:'linear-gradient(135deg,#1a1a2e,#16213e,#0f3460)',              l:'Cosmos'},
    {id:'bg-grad-2',  g:'linear-gradient(135deg,#020008,#1a0a3a,#2d0054)',              l:'Univers'},
    {id:'bg-grad-17', g:'linear-gradient(135deg,#0d0221,#190a4e,#2c0a6b)',              l:'Galaxie sombre'},
    {id:'bg-grad-18', g:'linear-gradient(135deg,#000428,#004e92)',                      l:'Nuit profonde'},
    /* Océans & Nature */
    {id:'bg-grad-19', g:'linear-gradient(135deg,#0b1d2e,#0e4d6e,#1a7a9a)',             l:'Océan'},
    {id:'bg-grad-20', g:'linear-gradient(135deg,#093028,#237a57)',                      l:'Mangrove'},
    {id:'bg-grad-4',  g:'linear-gradient(135deg,#0a1a0a,#1a3d1a,#2d7a2d)',             l:'Forêt'},
    {id:'bg-grad-12', g:'linear-gradient(135deg,#134e5e,#71b280)',                      l:'Jade'},
    {id:'bg-grad-21', g:'linear-gradient(135deg,#1a472a,#2d6a4f,#52b788)',             l:'Bambou'},
    {id:'bg-grad-22', g:'linear-gradient(135deg,#006994,#1cb5e0)',                      l:'Lagune'},
    /* Feux & Couchers */
    {id:'bg-grad-3',  g:'linear-gradient(135deg,#1a0a0a,#3d1515,#7a1010)',             l:'Rubis'},
    {id:'bg-grad-23', g:'linear-gradient(135deg,#1a0800,#7a2800,#c85000)',             l:'Coucher feu'},
    {id:'bg-grad-24', g:'linear-gradient(135deg,#870000,#190a05)',                      l:'Lave'},
    {id:'bg-grad-14', g:'linear-gradient(135deg,#c94b4b,#4b134f)',                      l:'Crépuscule'},
    {id:'bg-grad-25', g:'linear-gradient(135deg,#f7971e,#ffd200)',                      l:'Soleil'},
    /* Violets & Roses */
    {id:'bg-grad-5',  g:'linear-gradient(135deg,#1e0b2e,#4a1a6a,#6a2a9a)',             l:'Violet'},
    {id:'bg-grad-15', g:'linear-gradient(135deg,#005c97,#363795)',                      l:'Indigo'},
    {id:'bg-grad-16', g:'linear-gradient(135deg,#1d2671,#c33764)',                      l:'Galaxie rose'},
    {id:'bg-grad-26', g:'linear-gradient(135deg,#2a0a1a,#7a1a4a,#c0305a)',             l:'Rose sombre'},
    {id:'bg-grad-27', g:'linear-gradient(135deg,#4a00e0,#8e2de2)',                      l:'Électrique'},
    /* Aurores & Ambiances */
    {id:'bg-grad-11', g:'linear-gradient(135deg,#2d1b69,#11998e)',                      l:'Aurora'},
    {id:'bg-grad-9',  g:'linear-gradient(135deg,#0f2027,#203a43,#2c5364)',             l:'Arctique'},
    {id:'bg-grad-28', g:'linear-gradient(135deg,#005c97,#1cb5e0,#11998e)',             l:'Aurora bleue'},
    {id:'bg-grad-29', g:'linear-gradient(135deg,#0a3d62,#1e3799,#6a89cc)',             l:'Nuit polaire'},
    {id:'bg-grad-13', g:'linear-gradient(135deg,#373b44,#4286f4)',                      l:'Acier'},
    /* Chauds & Déserts */
    {id:'bg-grad-6',  g:'linear-gradient(135deg,#1a1000,#4a3000,#8a5a00)',             l:'Ambre'},
    {id:'bg-grad-30', g:'linear-gradient(135deg,#1c1400,#6b4400,#c88a00)',             l:'Sahara'},
    {id:'bg-grad-31', g:'linear-gradient(135deg,#2c1810,#5c2e18,#a05a30)',             l:'Terre cuite'},
    {id:'bg-grad-32', g:'linear-gradient(135deg,#3a2000,#8b5e00,#d4a017)',             l:'Or antique'},
    /* Clairs & Pastel */
    {id:'bg-grad-7',  g:'linear-gradient(135deg,#f8fafc,#dde8f5)',                     l:'Blanc'},
    {id:'bg-grad-8',  g:'linear-gradient(135deg,#ffecd2,#fcb69f)',                     l:'Pêche'},
    {id:'bg-grad-33', g:'linear-gradient(135deg,#e0f7fa,#b2ebf2,#80deea)',             l:'Ciel'},
    {id:'bg-grad-34', g:'linear-gradient(135deg,#f3e7e9,#e3eeff)',                     l:'Lavande'},
    {id:'bg-grad-35', g:'linear-gradient(135deg,#fdfbfb,#ebedee)',                     l:'Brume'},
    /* Spéciaux */
    {id:'bg-grad-36', g:'linear-gradient(135deg,#0f0c29,#302b63,#24243e)',             l:'Velours'},
    {id:'bg-grad-37', g:'linear-gradient(135deg,#000000,#1a1a2e)',                     l:'Minuit'},
    {id:'bg-grad-38', g:'linear-gradient(135deg,#003366,#006699,#0099cc)',             l:'Chimie'},
    {id:'bg-grad-39', g:'linear-gradient(135deg,#0f2027,#203a43,#2c5364)',             l:'Pro'},
    {id:'bg-grad-40', g:'linear-gradient(135deg,#16213e,#0f3460,#e94560)',             l:'Cyberpunk'},
];
const BG_LABEL = {}; BGS.forEach(b => BG_LABEL[b.id] = b.l);

const FALLBACKS = {
    'Segoe UI':'Tahoma,Geneva,Verdana,sans-serif',
    'Arial':'Helvetica,sans-serif','Calibri':'Candara,sans-serif',
    'Verdana':'Geneva,Tahoma,sans-serif','Tahoma':'Geneva,sans-serif',
    'Trebuchet MS':'Arial,sans-serif','Century Gothic':'Futura,sans-serif',
    'Gill Sans MT':'Gill Sans,sans-serif','Georgia':'"Times New Roman",serif',
    'Palatino Linotype':'Palatino,"Book Antiqua",serif',
    'Times New Roman':'Times,serif','Garamond':'"EB Garamond",Georgia,serif',
    'Book Antiqua':'Palatino,serif','Cambria':'Georgia,serif',
    'Courier New':'Courier,monospace','Consolas':'"Lucida Console",Monaco,monospace',
    'Lucida Console':'Monaco,Consolas,monospace','Lucida Sans Unicode':'Lucida Grande,sans-serif',
    'Impact':'Charcoal,sans-serif','Comic Sans MS':'cursive,sans-serif',
};

const AI_MAP = [
    {k:['ocean','mer','bleu','blue','sea','water','eau','marin'],   g:'linear-gradient(135deg,#0b1d2e,#0e4d6e,#1a7a9a)', n:'Océan'},
    {k:['foret','forest','nature','vert','green','jungle','arbre'], g:'linear-gradient(135deg,#0d2b0d,#1a4a1a,#2d7a2d)', n:'Forêt'},
    {k:['coucher','sunset','orange','soleil','sun','aube','lever'], g:'linear-gradient(135deg,#1a0800,#7a2800,#c85000)', n:'Coucher'},
    {k:['galaxie','galaxy','cosmos','espace','space','star','univers','nuit'], g:'linear-gradient(135deg,#020008,#1a0a3a,#2d0054)', n:'Galaxie'},
    {k:['aurora','aurore','boreale','nordique','arctique','arctic'], g:'linear-gradient(135deg,#0a1a2a,#0d4a2a,#1a6a4a)', n:'Aurora'},
    {k:['violet','purple','mauve','lilas','indigo','pourpre'],      g:'linear-gradient(135deg,#1e0b2e,#4a1a6a,#6a2a9a)', n:'Violet'},
    {k:['rouge','red','rubis','ruby','bordeaux','wine'],             g:'linear-gradient(135deg,#1a0000,#4a0000,#7a1010)', n:'Rubis'},
    {k:['rose','pink','corail','coral','saumon','salmon'],           g:'linear-gradient(135deg,#2a0a1a,#7a1a4a,#c0305a)', n:'Rose'},
    {k:['noir','black','sombre','dark','minuit','midnight'],         g:'linear-gradient(135deg,#050510,#0a0a1a,#0f0f2a)', n:'Nuit noire'},
    {k:['blanc','white','clair','light','neige','snow','nuage'],    g:'linear-gradient(135deg,#f0f4f8,#dde8f5,#c8dcea)', n:'Clair'},
    {k:['feu','fire','flamme','flame','volcan','lave','lava'],       g:'linear-gradient(135deg,#0a0000,#5a0a00,#c03000)', n:'Feu'},
    {k:['glace','ice','glacier','cyan','turquoise','aqua'],          g:'linear-gradient(135deg,#001a2a,#00486a,#007a9a)', n:'Glace'},
    {k:['or','gold','dore','golden','ambre','amber','jaune','yellow'],g:'linear-gradient(135deg,#1a1000,#4a3000,#8a5a00)', n:'Or'},
    {k:['science','tech','chimie','chemistry','engineering'],        g:'linear-gradient(135deg,#0a0e27,#0d2d5a,#0a4a8a)', n:'Science'},
    {k:['canva','design','creatif','creative','studio','art'],       g:'linear-gradient(135deg,#1a0a2e,#2d1b69,#4a2e8a)', n:'Design'},
    {k:['ppt','powerpoint','presentation','professionnel','pro','business'],g:'linear-gradient(135deg,#0f2027,#203a43,#2c5364)', n:'Pro'},
    {k:['gaz','gas','chimique','chemical','absorption','analyse'],   g:'linear-gradient(135deg,#003366,#006699,#0099cc)', n:'Chimie'},
    {k:['maroc','moroccan','sable','desert','sahara','beige'],       g:'linear-gradient(135deg,#1a1000,#6b4400,#c88a00)', n:'Sahara'},
];

/* ---- State ---- */
let S = {...DEF};
let _pendingG = null, _pendingN = null;

/* ---- Helpers ---- */
function lighten(hex){
    try{
        let r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);
        r=Math.min(255,r+60);g=Math.min(255,g+40);b=Math.min(255,b+40);
        return 'rgb('+r+','+g+','+b+')';
    }catch{return '#00D9FF';}
}

/* ================================================
   LOAD / SAVE
   ================================================ */
async function load(){
    try{
        const d = localStorage.getItem(KEY);
        if(d) S = {...DEF, ...JSON.parse(d)};
        
        // If logged in, load from server and merge
        if(window.isLoggedIn){
            try{
                const r = await fetch('/settings/get');
                if(r.ok){
                    const serverData = await r.json();
                    if(serverData.success && serverData.settings){
                        S = {...S, ...serverData.settings};
                        saveLocal(); // Update localStorage with server data
                    }
                }
            }catch(e){
                console.warn('Failed to load settings from server:', e);
            }
        }
    }catch(e){
        console.error('Failed to load settings:', e);
        S = {...DEF};
    }
}
function saveLocal(){ localStorage.setItem(KEY,JSON.stringify(S)); }
async function saveServer(){
    try{
        const r=await fetch('/settings/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(S)});
        return r.ok;
    }catch{return false;}
}

/* ================================================
   APPLY — Dynamic <style> tag (highest priority)
   ================================================ */
function applyAll(save){
    /* 1. Theme class */
    document.body.classList.remove('dark-mode','light-mode','theme-ocean','theme-forest','theme-sunset','theme-purple','theme-rose','theme-slate','theme-teal','theme-amber');
    document.body.classList.add(S.theme);

    /* 2. Inject/update dynamic style tag at END of <head> */
    let dyn = document.getElementById('sp-dynamic-vars');
    if(dyn) dyn.remove();
    dyn = document.createElement('style');
    dyn.id = 'sp-dynamic-vars';
    document.head.appendChild(dyn);

    /* Font Awesome families — MUST stay on icon elements */
    const FA = '"Font Awesome 6 Free","Font Awesome 5 Free",FontAwesome,"Font Awesome 6 Pro","Font Awesome 6 Brands","Font Awesome Free"';
    /* Icon selector — catches every FA usage pattern */
    const ICON_SEL = [
        'body i.fas','body i.far','body i.fab','body i.fal','body i.fad',
        'body .fa','body [class^="fa-"]','body [class*=" fa-"]',
        'body i[class*="fa"]','body span[class*="fa"]',
    ].join(',');

    const fontStack = "'" + S.fontFamily + "', " + S.fontFallback;
    const letterSpacing = S.letterSpacing !== undefined ? S.letterSpacing : 0;
    const fontWeight = S.fontWeight || 'normal';
    const lineHeight = S.lineHeight || 1.6;
    const noAnim = !S.animations ? '*,*::before,*::after{animation-duration:0s!important;transition-duration:0s!important}' : '';

    dyn.textContent = [
        /* Primary color everywhere */
        ':root{--primary-color:' + S.primaryColor + '!important;--secondary-color:' + lighten(S.primaryColor) + '!important}',
        'body,body.dark-mode,body.light-mode,body.theme-ocean,body.theme-forest,body.theme-sunset,' +
        'body.theme-purple,body.theme-rose,body.theme-slate,body.theme-teal,body.theme-amber,' +
        'body.theme-midnight,body.theme-cherry,body.theme-arctic,body.theme-coffee,body.theme-neon{' +
        '--primary-color:' + S.primaryColor + '!important;--secondary-color:' + lighten(S.primaryColor) + '!important}',

        /* Force color on key elements */
        'a,.nav-link.active,.nav-link:hover{color:' + S.primaryColor + '!important}',
        '.btn-primary,.sp-btn-save{background:' + S.primaryColor + '!important;border-color:' + S.primaryColor + '!important}',
        '.nav-link.active{border-left-color:' + S.primaryColor + '!important;background:' + S.primaryColor + '18!important}',
        '.sidebar-header::after,.brand-accent{background:' + S.primaryColor + '!important}',
        '.progress-bar,.badge.bg-primary{background:' + S.primaryColor + '!important}',

        /* === FONT FAMILY === */
        /* Step 1: set font on html/body */
        'html,body{font-family:' + fontStack + '!important}',
        /* Step 2: FIRST restore Font Awesome on all icon elements (before wildcard) */
        ICON_SEL + '{font-family:' + FA + '!important;font-style:normal}',
        /* Step 3: apply user font to text-bearing elements only (NOT i, span.fa) */
        'body p,body h1,body h2,body h3,body h4,body h5,body h6,' +
        'body div:not([class*="fa"]),body span:not([class*="fa"]),body td,body th,' +
        'body label,body a,body li,body button,body input,body select,body textarea,' +
        'body .nav-link,body .card-title,body .card-text,body .sidebar-brand-name,' +
        'body .topbar-title,body .page-title,body .section-title,' +
        'body .home-feature-text,body .feature-card *,body .info-card *,' +
        'body .stat-value,body .stat-label,body .result-value,' +
        'body table,body .modal *,body .dropdown-item' +
        '{font-family:' + fontStack + '!important}',
        /* Step 4: restore FA one more time (highest specificity wins ties) */
        'html body ' + ICON_SEL.replace(/body /g,'') + '{font-family:' + FA + '!important}',

        /* === FONT SIZE — proportional scale === */
        'html{font-size:' + S.fontSize + 'px!important}',
        'body{font-size:' + S.fontSize + 'px!important}',
        'body p,body li,body span:not([class*="fa"]),body div,body td,body th,body label{font-size:' + S.fontSize + 'px!important}',
        'body input,body select,body textarea,body button{font-size:' + S.fontSize + 'px!important}',
        'body h1{font-size:' + Math.round(S.fontSize*2.1) + 'px!important}',
        'body h2{font-size:' + Math.round(S.fontSize*1.75) + 'px!important}',
        'body h3{font-size:' + Math.round(S.fontSize*1.45) + 'px!important}',
        'body h4{font-size:' + Math.round(S.fontSize*1.2) + 'px!important}',
        'body h5,body h6{font-size:' + Math.round(S.fontSize*1.05) + 'px!important}',
        'body .nav-link,body .sidebar-brand-name{font-size:' + S.fontSize + 'px!important}',

        /* === FONT WEIGHT === */
        'body p,body li,body div,body span:not([class*="fa"]),body label,body .nav-link{font-weight:' + fontWeight + '!important}',
        'body h1,body h2,body h3,body h4,body h5,body h6{font-weight:' + (fontWeight==='300'?'500':fontWeight==='700'?'800':fontWeight==='900'?'900':'600') + '!important}',

        /* === LETTER SPACING === */
        'body p,body li,body div,body span:not([class*="fa"]),body label,body a,body .nav-link{letter-spacing:' + letterSpacing + 'px!important}',
        'body h1,body h2,body h3,body h4,body h5,body h6{letter-spacing:' + (letterSpacing+0.5) + 'px!important}',
        '.sp-section-title,body .topbar-title{letter-spacing:1px!important}',

        /* === LINE HEIGHT === */
        'body p,body li{line-height:' + lineHeight + '!important}',

        /* Settings panel — always readable */
        '#settings-panel,#settings-panel *{font-family:"Segoe UI",Tahoma,sans-serif!important;letter-spacing:normal!important}',
        '#settings-panel .sp-section-title{font-size:0.72rem!important;font-weight:700!important}',
        '#settings-panel .sp-label,#settings-panel .sp-slider-val,#settings-panel .sp-font-name{font-size:0.8rem!important}',
        '#settings-panel .sp-font-sample{font-size:1.1rem!important}',
        '#settings-panel .sp-theme-card span,#settings-panel .sp-bg-option span{font-size:0.72rem!important}',
        /* Keep FA icons inside settings panel too */
        '#settings-panel i.fas,#settings-panel i.far,#settings-panel i.fab{font-family:' + FA + '!important}',

        /* Sidebar compact */
        S.sidebarCompact ? '.sidebar{width:70px!important}.sidebar .sidebar-brand-name,.sidebar .nav-link span,.sidebar .sidebar-footer{display:none!important}.sidebar .nav-link{justify-content:center!important}.main-content{margin-left:70px!important}' : '',

        noAnim,
    ].join('\n');

    /* 3. Background */
    applyBg();

    /* 4. Save */
    if(save) saveLocal();
}

function applyBg(){
    /* Remove old bg style tag */
    const old = document.getElementById('sp-bg-dyn');
    if(old) old.remove();

    let bgValue = '';
    if(S.background === 'bg-custom' && S.customBgGradient){
        bgValue = S.customBgGradient;
    } else {
        const found = BGS.find(b => b.id === S.background);
        if(found && found.g) bgValue = found.g;
    }

    if(bgValue){
        const s = document.createElement('style');
        s.id = 'sp-bg-dyn';
        s.textContent = 'html body,html body.dark-mode,html body.light-mode,' +
            'html body.theme-ocean,html body.theme-forest,html body.theme-sunset,' +
            'html body.theme-purple,html body.theme-rose,html body.theme-slate,' +
            'html body.theme-teal,html body.theme-amber{background:' + bgValue + '!important}';
        document.head.appendChild(s);
    }
}

/* ================================================
   BUILD PANEL BODY
   ================================================ */
function buildBody(){
    const el = qs('sp-body-content');
    if(!el) return;

    el.innerHTML =
        /* THEMES */
        sec('palette','Thème',
            '<div class="sp-themes">' +
            THEMES.map(t =>
                '<div class="sp-theme-card" data-theme="'+t.id+'">' +
                '<div style="width:40px;height:26px;border-radius:5px;overflow:hidden;display:flex;flex-direction:column;margin:0 auto 5px">' +
                '<div style="flex:0 0 40%;background:'+t.top+'"></div>' +
                '<div style="flex:0 0 60%;background:'+t.bot+'"></div></div>' +
                '<span>'+t.label+'</span></div>'
            ).join('') + '</div>') +

        /* COLORS */
        sec('circle','Couleur principale',
            '<div class="sp-colors">' +
            COLORS.map(c =>
                '<div class="sp-color-swatch" data-color="'+c.c+'" style="background:'+c.c+'" title="'+c.l+'"></div>'
            ).join('') +
            '<input type="color" id="sp-custom-color" value="'+S.primaryColor+'" title="Couleur libre" ' +
            'style="width:30px;height:30px;border-radius:50%;border:3px solid var(--border-color);cursor:pointer;padding:0;background:none">' +
            '</div>') +

        /* FONTS */
        sec('font','Police d\'écriture',
            '<div class="sp-font-grid">' +
            FONTS.map(f =>
                '<div class="sp-font-card" data-font="'+f.k+'" style="font-family:\''+f.k+'\',sans-serif">' +
                '<div class="sp-font-sample" style="font-size:1.1rem;margin-bottom:2px">Aa</div>' +
                '<div class="sp-font-name" style="font-size:0.72rem">'+f.l+'</div></div>'
            ).join('') + '</div>') +

        /* FONT SIZE */
        sec('text-height','Taille du texte',
            '<div class="sp-slider-row">' +
            '<span class="sp-label" style="font-size:11px!important">A</span>' +
            '<input type="range" class="sp-slider" id="sp-font-size" min="12" max="20" step="1" value="'+S.fontSize+'">' +
            '<span class="sp-label" style="font-size:19px!important">A</span>' +
            '<span class="sp-slider-val" id="sp-font-size-val">'+S.fontSize+'px</span>' +
            '</div>') +

        /* BACKGROUNDS */
        sec('image','Fond d\'écran',
            '<div class="sp-bg-grid">' +
            BGS.map(b =>
                '<div class="sp-bg-option" data-bg="'+b.id+'" title="'+b.l+'" ' +
                'style="'+(b.g?'background:'+b.g:'background:var(--card-bg);border:2px dashed var(--border-color)')+'">' +
                '<span class="sp-bg-check"><i class="fas fa-check"></i></span>' +
                '<span style="position:absolute;bottom:2px;left:0;right:0;text-align:center;' +
                'font-size:8px;font-weight:700;text-shadow:0 1px 3px rgba(0,0,0,0.8);' +
                'color:'+(b.id==='bg-none'?'var(--text-muted)':'rgba(255,255,255,0.95)')+'">'+b.l+'</span>' +
                '</div>'
            ).join('') + '</div>' +

            /* AI Generator */
            '<div style="margin-top:14px">' +
            '<div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:7px;display:flex;align-items:center;gap:5px">' +
            '<i class="fas fa-magic" style="color:var(--primary-color)"></i> Générer un fond par mot-clé</div>' +
            '<div style="display:flex;gap:6px">' +
            '<input type="text" id="sp-ai-input" placeholder="océan, forêt, feu, galaxie, science..." ' +
            'style="flex:1;padding:8px 10px;border-radius:8px;border:1.5px solid var(--border-color);' +
            'background:var(--card-bg)!important;color:var(--text-primary)!important;font-size:0.82rem;outline:none">' +
            '<button id="sp-ai-btn" style="padding:8px 14px;border-radius:8px;border:none;' +
            'background:var(--primary-color);color:#fff;font-size:0.82rem;cursor:pointer;white-space:nowrap;font-weight:600">' +
            '<i class="fas fa-magic"></i> Générer</button></div>' +
            '<div id="sp-ai-preview-wrap" style="display:none;margin-top:8px">' +
            '<div id="sp-ai-preview" style="height:46px;border-radius:8px;cursor:pointer;' +
            'border:2px solid var(--primary-color);display:flex;align-items:center;justify-content:center;' +
            'font-size:0.8rem;color:#fff;font-weight:700;text-shadow:0 1px 4px rgba(0,0,0,0.7)" ' +
            'onclick="window._SP&&window._SP.applyAiBg()">✓ Cliquer pour appliquer</div></div>' +
            '<div id="sp-ai-msg" style="font-size:0.75rem;margin-top:5px;min-height:18px"></div>' +
            '</div>') +

        /* INTERFACE */
        sec('columns','Interface',
            toggle('sp-compact','Sidebar compacte',S.sidebarCompact) +
            toggle('sp-anim','Animations',S.animations)) +

        /* ADVANCED TYPOGRAPHY */
        sec('sliders-h','Typographie avancée',
            /* Font Weight */
            '<div style="margin-bottom:12px">' +
            '<div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:6px;font-weight:600">⚖️ Graisse du texte</div>' +
            '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:5px">' +
            [{v:'300',l:'Léger'},{v:'normal',l:'Normal'},{v:'500',l:'Moyen'},{v:'600',l:'Semi-gras'},{v:'700',l:'Gras'},{v:'900',l:'Très gras'}].map(fw =>
                '<div class="sp-fw-card" data-fw="'+fw.v+'" style="padding:6px 4px;border-radius:6px;border:2px solid var(--border-color);' +
                'text-align:center;cursor:pointer;font-size:0.72rem;font-weight:'+fw.v+';transition:all 0.2s">'+fw.l+'</div>'
            ).join('') + '</div></div>' +

            /* Letter Spacing */
            '<div style="margin-bottom:12px">' +
            '<div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:6px;font-weight:600">↔️ Espacement des lettres</div>' +
            '<div class="sp-slider-row">' +
            '<span class="sp-label" style="font-size:10px!important;letter-spacing:0px">Aa</span>' +
            '<input type="range" class="sp-slider" id="sp-letter-spacing" min="-1" max="5" step="0.5" value="'+( S.letterSpacing||0)+'">' +
            '<span class="sp-label" style="font-size:10px!important;letter-spacing:4px">Aa</span>' +
            '<span class="sp-slider-val" id="sp-ls-val">'+(S.letterSpacing||0)+'px</span>' +
            '</div></div>' +

            /* Line Height */
            '<div>' +
            '<div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:6px;font-weight:600">↕️ Interligne</div>' +
            '<div class="sp-slider-row">' +
            '<span class="sp-label" style="font-size:10px!important">1.2</span>' +
            '<input type="range" class="sp-slider" id="sp-line-height" min="1.2" max="2.4" step="0.1" value="'+(S.lineHeight||1.6)+'">' +
            '<span class="sp-label" style="font-size:10px!important">2.4</span>' +
            '<span class="sp-slider-val" id="sp-lh-val">'+(S.lineHeight||1.6)+'</span>' +
            '</div></div>');

    syncUI();
}

function sec(icon, title, content){
    return '<div class="sp-section">' +
        '<div class="sp-section-title"><i class="fas fa-'+icon+'"></i> '+title+'</div>' +
        content + '</div>';
}
function toggle(id, label, checked){
    return '<div class="sp-row"><span class="sp-label">'+label+'</span>' +
        '<label class="sp-toggle"><input type="checkbox" id="'+id+'"'+(checked?' checked':'')+' >' +
        '<span class="sp-toggle-slider"></span></label></div>';
}

/* ================================================
   SYNC UI STATE
   ================================================ */
function syncUI(){
    qsa('.sp-theme-card').forEach(e => e.classList.toggle('active', e.dataset.theme === S.theme));
    qsa('.sp-color-swatch').forEach(e => e.classList.toggle('active', e.dataset.color.toLowerCase() === S.primaryColor.toLowerCase()));
    const pk = qs('sp-custom-color'); if(pk) pk.value = S.primaryColor;
    qsa('.sp-font-card').forEach(e => e.classList.toggle('active', e.dataset.font === S.fontFamily));
    const sl = qs('sp-font-size'); if(sl) sl.value = S.fontSize;
    const sv = qs('sp-font-size-val'); if(sv) sv.textContent = S.fontSize + 'px';
    qsa('.sp-bg-option').forEach(e => e.classList.toggle('active', e.dataset.bg === S.background));
    const cp = qs('sp-compact'); if(cp) cp.checked = !!S.sidebarCompact;
    const an = qs('sp-anim'); if(an) an.checked = !!S.animations;
    /* Advanced typo */
    qsa('.sp-fw-card').forEach(e => {
        e.classList.toggle('active', e.dataset.fw === (S.fontWeight||'normal'));
        e.style.borderColor = e.dataset.fw === (S.fontWeight||'normal') ? S.primaryColor : '';
        e.style.background = e.dataset.fw === (S.fontWeight||'normal') ? S.primaryColor+'20' : '';
        e.style.color = e.dataset.fw === (S.fontWeight||'normal') ? S.primaryColor : '';
    });
    const ls = qs('sp-letter-spacing'); if(ls) ls.value = S.letterSpacing||0;
    const lsv = qs('sp-ls-val'); if(lsv) lsv.textContent = (S.letterSpacing||0)+'px';
    const lh = qs('sp-line-height'); if(lh) lh.value = S.lineHeight||1.6;
    const lhv = qs('sp-lh-val'); if(lhv) lhv.textContent = S.lineHeight||1.6;
}

/* ================================================
   OPEN / CLOSE
   ================================================ */
function openPanel(){
    const p=qs('settings-panel'), o=qs('settings-overlay');
    if(p) p.classList.add('open');
    if(o) o.classList.add('active');
}
function closePanel(){
    const p=qs('settings-panel'), o=qs('settings-overlay');
    if(p) p.classList.remove('open');
    if(o) o.classList.remove('active');
}

/* ================================================
   AI BACKGROUND GENERATOR
   ================================================ */
function genBg(kw){
    const k = kw.toLowerCase()
        .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
        .replace(/[^a-z0-9 ]/g,'');
    for(const e of AI_MAP){
        if(e.k.some(key => k.includes(key)))
            return {g:e.g, n:e.n};
    }
    /* Fallback: hash-based color */
    const h=[...k].reduce((a,c)=>(a<<5)-a+c.charCodeAt(0),0);
    const h1=Math.abs(h)%360, h2=(h1+55)%360;
    return {g:'linear-gradient(135deg,hsl('+h1+',65%,10%),hsl('+h2+',55%,22%))',n:'"'+kw+'"'};
}
function handleAiBtn(){
    const inp=qs('sp-ai-input'), msg=qs('sp-ai-msg'),
          wrap=qs('sp-ai-preview-wrap'), pre=qs('sp-ai-preview'),
          btn=qs('sp-ai-btn');
    const kw = inp ? inp.value.trim() : '';
    if(!kw){
        if(msg){msg.style.color='#ef4444';msg.textContent='⚠️ Entrez un mot-clé (ex: océan, feu, galaxie).';}
        return;
    }
    if(btn){btn.innerHTML='<i class="fas fa-spinner fa-spin"></i>';btn.disabled=true;}
    setTimeout(()=>{
        const r=genBg(kw);
        _pendingG=r.g; _pendingN=r.n;
        if(pre){pre.style.background=r.g;pre.textContent='✓ Appliquer "'+r.n+'"';}
        if(wrap) wrap.style.display='block';
        if(msg){msg.style.color='#10b981';msg.textContent='✨ Fond "'+r.n+'" généré ! Cliquez l\'aperçu pour appliquer.';}
        if(btn){btn.innerHTML='<i class="fas fa-magic"></i> Générer';btn.disabled=false;}
    },400);
}
function applyAiBg(){
    if(!_pendingG) return;
    S.background='bg-custom'; S.customBgGradient=_pendingG; S.customBgName=_pendingN;
    applyBg(); // uses the style tag now
    qsa('.sp-bg-option').forEach(e=>e.classList.remove('active'));
    const msg=qs('sp-ai-msg');
    if(msg){msg.style.color='#10b981';msg.textContent='✅ Fond "'+_pendingN+'" appliqué !';}
    saveLocal();
}

/* ================================================
   SAVE — result modal + reload
   ================================================ */
async function handleSave(){
    const btn=qs('sp-save-btn');
    if(btn){btn.disabled=true;btn.innerHTML='<i class="fas fa-spinner fa-spin"></i> Sauvegarde...';}
    saveLocal();
    const ok=await saveServer();
    if(btn){btn.disabled=false;btn.innerHTML='<i class="fas fa-save"></i> Sauvegarder';}
    showResult(ok);
}

function R(label,val){
    return '<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid var(--border-color)">' +
        '<span style="font-size:0.78rem;color:var(--text-secondary)">'+label+'</span>' +
        '<span style="font-size:0.78rem;color:var(--text-primary);font-weight:600">'+val+'</span></div>';
}

function showResult(ok){
    const old=qs('sp-result-modal'); if(old) old.remove();
    const tLabel = (THEMES.find(t=>t.id===S.theme)||{}).label||S.theme;
    const bgLabel = S.background==='bg-custom'?(S.customBgName||'Personnalisé'):(BG_LABEL[S.background]||S.background);
    const modal=document.createElement('div');
    modal.id='sp-result-modal';
    modal.style.cssText='position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.7);backdrop-filter:blur(5px)';
    modal.innerHTML=
        '<div style="background:var(--card-bg,#1a1f3a);border:1px solid var(--border-color);border-radius:20px;'+
        'padding:30px;max-width:390px;width:92%;box-shadow:0 24px 64px rgba(0,0,0,0.6);text-align:center;animation:slideUp .3s ease">'+
        '<div style="font-size:48px;margin-bottom:10px">'+(ok?'✅':'💾')+'</div>'+
        '<h4 style="margin:0 0 6px;color:var(--primary-color);font-size:1.1rem">'+(ok?'Paramètres sauvegardés !':'Sauvegardé localement')+'</h4>'+
        '<p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:18px">La page se recharge dans <span id="sp-cd">4</span>s…</p>'+
        '<div style="background:rgba(0,102,255,0.08);border:1px solid rgba(0,102,255,0.2);border-radius:12px;padding:14px;margin-bottom:18px;text-align:left">'+
        '<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text-muted);margin-bottom:10px">📋 Résumé des paramètres</div>'+
        R('🎨 Thème', tLabel)+
        R('🔵 Couleur','<span style="display:inline-flex;align-items:center;gap:5px"><span style="width:13px;height:13px;border-radius:50%;background:'+S.primaryColor+';display:inline-block;border:1px solid rgba(255,255,255,0.2)"></span>'+S.primaryColor+'</span>')+
        R('🔤 Police', S.fontFamily)+
        R('📏 Taille texte', S.fontSize+'px')+
        R('🖼️ Fond', bgLabel)+
        R('✨ Animations', S.animations?'Activées':'Désactivées')+
        '</div>'+
        '<button id="sp-result-close" style="background:var(--primary-color);color:#fff;border:none;border-radius:10px;padding:11px 24px;font-size:0.9rem;font-weight:600;cursor:pointer;width:100%">Fermer et recharger ✓</button>'+
        '</div><style>@keyframes slideUp{from{transform:translateY(28px);opacity:0}to{transform:translateY(0);opacity:1}}</style>';
    document.body.appendChild(modal);
    let t=4; const cd=modal.querySelector('#sp-cd');
    const timer=setInterval(()=>{t--;if(cd)cd.textContent=t;if(t<=0){clearInterval(timer);doReload(modal);}},1000);
    modal.querySelector('#sp-result-close').addEventListener('click',()=>{clearInterval(timer);doReload(modal);});
    modal.addEventListener('click',e=>{if(e.target===modal){clearInterval(timer);doReload(modal);}});
}
function doReload(modal){modal.remove();setTimeout(()=>window.location.reload(),150);}
function handleReset(){if(!confirm('Réinitialiser tous les paramètres ?')) return; S={...DEF}; applyAll(true); syncUI();}

/* ================================================
   EVENTS
   ================================================ */
function bindEvents(){
    document.addEventListener('click', function(e){
        /* Theme card */
        const tc=e.target.closest('.sp-theme-card[data-theme]');
        if(tc&&qs('settings-panel')&&qs('settings-panel').contains(tc)){
            S.theme=tc.dataset.theme; applyAll(true); syncUI(); return;
        }
        /* Color swatch */
        const sw=e.target.closest('.sp-color-swatch');
        if(sw){S.primaryColor=sw.dataset.color;applyAll(true);syncUI();return;}
        /* Font card */
        const fc=e.target.closest('.sp-font-card');
        if(fc&&qs('settings-panel')&&qs('settings-panel').contains(fc)){
            S.fontFamily=fc.dataset.font;
            S.fontFallback = (FALLBACKS && FALLBACKS[fc.dataset.font]) || 'Tahoma, Geneva, Verdana, sans-serif';
            applyAll(true);syncUI();return;
        }
        /* BG option */
        const bg=e.target.closest('.sp-bg-option');
        if(bg&&qs('settings-panel')&&qs('settings-panel').contains(bg)){
            S.background=bg.dataset.bg;applyBg();saveLocal();syncUI();return;
        }
        /* Close */
        if(e.target.closest('#sp-close-btn')){closePanel();return;}
        if(e.target.id==='settings-overlay'){closePanel();return;}
        /* Font weight card */
        const fwc = e.target.closest('.sp-fw-card');
        if(fwc){S.fontWeight=fwc.dataset.fw;applyAll(true);syncUI();return;}
        /* Save / Reset */
        if(e.target.closest('#sp-save-btn')){handleSave();return;}
        if(e.target.closest('#sp-reset-btn')){handleReset();return;}
        /* AI */
        if(e.target.closest('#sp-ai-btn')){handleAiBtn();return;}
    });

    document.addEventListener('input', function(e){
        if(e.target.id==='sp-font-size'){
            S.fontSize=parseInt(e.target.value);
            const v=qs('sp-font-size-val');if(v)v.textContent=S.fontSize+'px';
            applyAll(true);
        }
        if(e.target.id==='sp-custom-color'){S.primaryColor=e.target.value;applyAll(true);syncUI();}
        if(e.target.id==='sp-compact'){S.sidebarCompact=e.target.checked;applyAll(true);}
        if(e.target.id==='sp-anim'){S.animations=e.target.checked;applyAll(true);}
        /* Letter spacing */
        if(e.target.id==='sp-letter-spacing'){
            S.letterSpacing=parseFloat(e.target.value);
            const v=qs('sp-ls-val');if(v)v.textContent=S.letterSpacing+'px';
            applyAll(true);
        }
        /* Line height */
        if(e.target.id==='sp-line-height'){
            S.lineHeight=parseFloat(e.target.value);
            const v=qs('sp-lh-val');if(v)v.textContent=S.lineHeight;
            applyAll(true);
        }
        /* AI input Enter key */
        if(e.target.id==='sp-ai-input' && e.key==='Enter'){handleAiBtn();}
    });

    /* Also handle Enter on AI input */
    document.addEventListener('keydown', function(e){
        if(e.target.id==='sp-ai-input' && e.key==='Enter'){handleAiBtn();}
    });
}

/* ================================================
   EXTRA THEME CSS
   ================================================ */
function injectThemeCSS(){
    if(qs('sp-theme-css')) return;
    const s=document.createElement('style');
    s.id='sp-theme-css';
    s.textContent=
        /* Dark themes */
        'body.theme-ocean{--dark-bg:#0b1d2e;--card-bg:#12344d;--border-color:#1a4a6e;--text-primary:#e0f2fe;--text-secondary:#7dd3fc;--text-muted:#38bdf8;background:linear-gradient(135deg,#0b1d2e,#12344d)}'+
        'body.theme-forest{--dark-bg:#0d1f0d;--card-bg:#1a2e1a;--border-color:#2d4a2d;--text-primary:#d1fae5;--text-secondary:#6ee7b7;--text-muted:#34d399;background:linear-gradient(135deg,#0d1f0d,#1a2e1a)}'+
        'body.theme-sunset{--dark-bg:#1f0d05;--card-bg:#2e1a0e;--border-color:#4a2e1a;--text-primary:#fef3c7;--text-secondary:#fcd34d;--text-muted:#f59e0b;background:linear-gradient(135deg,#1f0d05,#2e1a0e)}'+
        'body.theme-purple{--dark-bg:#1e0b2e;--card-bg:#2e1a4a;--border-color:#4a2e6e;--text-primary:#ede9fe;--text-secondary:#c4b5fd;--text-muted:#a78bfa;background:linear-gradient(135deg,#1e0b2e,#2e1a4a)}'+
        'body.theme-rose{--dark-bg:#1a0510;--card-bg:#2e0f1e;--border-color:#5a1a3a;--text-primary:#fce7f3;--text-secondary:#f9a8d4;--text-muted:#f472b6;background:linear-gradient(135deg,#1a0510,#2e0f1e)}'+
        'body.theme-slate{--dark-bg:#0f172a;--card-bg:#1e293b;--border-color:#334155;--text-primary:#f1f5f9;--text-secondary:#94a3b8;--text-muted:#64748b;background:linear-gradient(135deg,#0f172a,#1e293b)}'+
        'body.theme-teal{--dark-bg:#042f2e;--card-bg:#134e4a;--border-color:#0d9488;--text-primary:#ccfbf1;--text-secondary:#5eead4;--text-muted:#2dd4bf;background:linear-gradient(135deg,#042f2e,#134e4a)}'+
        'body.theme-amber{--dark-bg:#1c1400;--card-bg:#3d2e00;--border-color:#6b5000;--text-primary:#fef9c3;--text-secondary:#fde047;--text-muted:#facc15;background:linear-gradient(135deg,#1c1400,#3d2e00)}'+
        'body.theme-cyber{--dark-bg:#0d0221;--card-bg:#190a4e;--border-color:#4a1a8e;--text-primary:#e0d7ff;--text-secondary:#a78bfa;--text-muted:#7c3aed;background:linear-gradient(135deg,#0d0221,#190a4e)}'+
        'body.theme-matrix{--dark-bg:#001100;--card-bg:#003300;--border-color:#005500;--text-primary:#00ff00;--text-secondary:#00cc00;--text-muted:#009900;background:linear-gradient(135deg,#001100,#003300)}'+
        'body.theme-neon{--dark-bg:#0a0000;--card-bg:#1a0010;--border-color:#500030;--text-primary:#ffd6e7;--text-secondary:#ff6eb4;--text-muted:#ff1493;background:linear-gradient(135deg,#0a0000,#2a0000)}'+
        /* Light themes */
        'body.theme-mint{--dark-bg:#ecfdf5;--card-bg:#d1fae5;--border-color:#a7f3d0;--text-primary:#065f46;--text-secondary:#047857;--text-muted:#059669;background:linear-gradient(135deg,#ecfdf5,#d1fae5)}'+
        'body.theme-sky{--dark-bg:#f0f9ff;--card-bg:#e0f2fe;--border-color:#bae6fd;--text-primary:#0c4a6e;--text-secondary:#075985;--text-muted:#0284c7;background:linear-gradient(135deg,#f0f9ff,#e0f2fe)}'+
        'body.theme-peach{--dark-bg:#fff7ed;--card-bg:#fed7aa;--border-color:#fdba74;--text-primary:#7c2d12;--text-secondary:#9a3412;--text-muted:#c2410c;background:linear-gradient(135deg,#fff7ed,#fed7aa)}'+
        'body.theme-lavender{--dark-bg:#faf5ff;--card-bg:#ede9fe;--border-color:#ddd6fe;--text-primary:#4c1d95;--text-secondary:#5b21b6;--text-muted:#6d28d9;background:linear-gradient(135deg,#faf5ff,#ede9fe)}';
    document.head.appendChild(s);
}

/* ================================================
   INIT
   ================================================ */
async function init(){
    await load();
    injectThemeCSS();
    applyAll(false);
    buildBody();
    bindEvents();

    /* Open button — capture phase beats all other handlers */
    const openBtn = document.getElementById('settings-open-btn');
    if(openBtn){
        openBtn.removeAttribute('onclick');
        openBtn.addEventListener('click', function(e){
            e.preventDefault();
            e.stopPropagation();
            openPanel();
        }, true);
    }

    /* AI button direct listener (added after buildBody so element exists) */
    const aiBtn = document.getElementById('sp-ai-btn');
    if(aiBtn){
        aiBtn.addEventListener('click', function(e){
            e.preventDefault();
            e.stopPropagation();
            handleAiBtn();
        });
    }

    /* Also support Enter key in AI input */
    const aiInput = document.getElementById('sp-ai-input');
    if(aiInput){
        aiInput.addEventListener('keydown', function(e){
            if(e.key === 'Enter'){ e.preventDefault(); handleAiBtn(); }
        });
    }

    /* Expose globally */
    window._SP = {openPanel, closePanel, applyAiBg, genBg};
}

if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

})();
