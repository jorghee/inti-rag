"""HTML fixtures simulating SPIJ portal content for testing.

These fixtures replicate the real DOM structure observed in the SPIJ
(Sistema Peruano de Informacion Juridica) web portal, including:
- Navigation chrome and toolbar elements
- Concordance/annotation blocks
- Structural headings (Libro, Titulo, Capitulo)
- Individual article blocks with sumillas
- Footer/boilerplate text

Reference: docs/modules/legal-ingestion.md
"""

# A realistic SPIJ page fragment containing a Book with two articles
SPIJ_CIVIL_CODE_FRAGMENT = """\
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>SPIJ - Codigo Civil</title>
    <script src="/assets/analytics.js"></script>
    <style>
        .norm-text-body { font-family: Arial, sans-serif; }
        .article-number { font-weight: bold; }
    </style>
    <link rel="stylesheet" href="/css/spij.css">
</head>
<body>
<app-root>
<div class="main-container">

    <header class="header-spij">
        <div class="logo-minjus">MINJUSDH Logo</div>
        <nav class="nav-menu">
            <a href="/">Inicio</a>
            <a href="/legislacion">Legislacion</a>
        </nav>
    </header>

    <main class="content-wrapper">

        <aside class="sidebar-filters">
            <div class="search-box-lateral">
                <input type="text" placeholder="Buscar...">
            </div>
            <tree-view class="norm-index-tree">
                <ul>
                    <li>Libro I: Derechos de las Personas</li>
                    <li>Libro II: Acto Juridico</li>
                </ul>
            </tree-view>
        </aside>

        <section class="document-viewer-container">
            <div class="toolbar-actions">
                <button class="btn-download-pdf">PDF</button>
                <button class="btn-download-word">Word</button>
                <button class="btn-print">Imprimir</button>
                <button class="btn-share">Compartir</button>
            </div>

            <article class="norm-text-body">
                <!-- Document metadata header -->
                <div class="norm-header-info">
                    <h1 class="norm-title">CODIGO CIVIL - DECRETO LEGISLATIVO N\u00ba 295</h1>
                    <span class="update-date">Actualizado y concordado al 15 de marzo de 2024</span>
                </div>

                <div class="book-container" data-book="Libro I">
                    <h2 class="book-title">LIBRO I: DERECHOS DE LAS PERSONAS</h2>

                    <div class="title-container">
                        <h3>TITULO I: Principio de la Persona</h3>

                        <div class="article-block" id="art-1">
                            <span class="article-number">Art\u00edculo 1.-</span>
                            <span class="article-sumilla">Persona humana como sujeto de derecho</span>
                            <p class="article-content">La persona humana es sujeto de derecho desde su nacimiento.</p>
                            <p class="article-content">La vida humana comienza con la concepci\u00f3n. El concebido es sujeto de derecho para todo cuanto le favorece. La atribuci\u00f3n de derechos patrimoniales est\u00e1 condicionada a que nazca vivo.</p>

                            <div class="concordances-section">
                                <span class="concordance-label">Concordancias:</span>
                                <ul>
                                    <li><a href="/norma/123">Constituci\u00f3n Pol\u00edtica del Per\u00fa, Art. 2</a></li>
                                    <li><a href="/norma/456">C\u00f3digo de los Ni\u00f1os y Adolescentes, Art. I</a></li>
                                </ul>
                            </div>
                        </div>

                        <div class="article-block" id="art-2">
                            <span class="article-number">Art\u00edculo  2 .-</span>
                            <span class="article-sumilla">Reconocimiento del embarazo o parto</span>
                            <p class="article-content">La mujer puede solicitar judicialmente el reconocimiento de su embarazo o del parto, con citaci\u00f3n de las personas que tengan inter\u00e9s en el nacimiento.</p>

                            <div class="concordances-section">
                                <span class="concordance-label">Concordancias:</span>
                                <ul>
                                    <li><a href="/norma/789">C\u00f3digo Procesal Civil, Art. 2</a></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </article>
        </section>

        <aside class="contextual-sidebar">
            <div class="modifications-history">
                <h4>Historial de Modificaciones</h4>
                <p>Modificado por Ley N\u00ba 30007</p>
            </div>
        </aside>

    </main>

    <footer class="footer-spij">
        <p>Ministerio de Justicia y Derechos Humanos - MINJUSDH</p>
        <p>Todos los derechos reservados</p>
    </footer>

</div>
</app-root>

<!-- Google Analytics -->
<script>
    (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;})(window,document,'script','https://www.google-analytics.com/analytics.js','ga');
</script>
<noscript>
    <img src="https://www.google-analytics.com/collect?v=1" alt="">
</noscript>
</body>
</html>
"""

# A fragment with multiple structural levels and typographic Unicode
SPIJ_MULTI_LEVEL_FRAGMENT = """\
<html>
<body>
<article class="norm-text-body">
    <div class="book-container">
        <h2>LIBRO VII: Fuentes de las Obligaciones</h2>

        <div class="section-container">
            <h3>Secci\u00f3n Segunda: Contratos Nominados</h3>

            <div class="title-container">
                <h4>T\u00edtulo I: Compraventa</h4>

                <div class="chapter-container">
                    <h5>Cap\u00edtulo Primero: Disposiciones Generales</h5>

                    <div class="article-block">
                        <span class="article-number">ART\u00cdCULO 1529.-</span>
                        <p class="article-content">Por la compraventa el vendedor se obliga a transferir la propiedad de un bien al comprador y \u00e9ste a pagar su precio en dinero.</p>
                    </div>

                    <div class="article-block">
                        <span class="article-number">Art\u00edculo 1530.-</span>
                        <p class="article-content">Los gastos de entrega son de cargo del vendedor y los gastos de transporte a un lugar diferente del de cumplimiento son de cargo del comprador, salvo pacto diverso.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</article>
</body>
</html>
"""

# Minimal fragment with only plain text (no HTML)
PLAIN_TEXT_FRAGMENT = """\
LIBRO I: DERECHOS DE LAS PERSONAS

TITULO I: Principio de la Persona

Art\u00edculo 1.- La persona humana es sujeto de derecho desde su nacimiento.

Art\u00edculo 2.- La mujer puede solicitar judicialmente el reconocimiento de su embarazo o del parto.
"""

# Fragment with extensive Unicode typographic characters
UNICODE_HEAVY_FRAGMENT = """\
<html><body>
<p>\u201cEl concebido es sujeto de derecho\u201d \u2013seg\u00fan el Art\u00edculo 1\u2013 para todo cuanto le favorece\u2026</p>
<p>La atribuci\u00f3n de derechos patrimoniales est\u00e1 condicionada a que nazca vivo\u00ad.</p>
<p>V\u00e9ase:\u00a0Art.\u00a01\u00a0del\u00a0C\u00f3digo\u00a0Civil</p>
</body></html>
"""

# Fragment with only boilerplate and no legal content
BOILERPLATE_ONLY_FRAGMENT = """\
<html>
<body>
<header class="header-spij">
    <div class="logo-minjus">MINJUSDH</div>
</header>
<footer class="footer-spij">
    <p>Ministerio de Justicia y Derechos Humanos - MINJUSDH</p>
    <p>Sistema Peruano de Informacion Juridica - SPIJ</p>
    <p>Todos los derechos reservados</p>
</footer>
</body>
</html>
"""

# Fragment simulating an article with mixed article marker formats
INCONSISTENT_MARKERS_FRAGMENT = """\
<html><body>
<div class="norm-text-body">
    <p>Articulo 100.- Primer articulo con formato mixto.</p>
    <p>ART\u00cdCULO  101 .- Segundo articulo con espacios extra.</p>
    <p>art\u00edculo 102.-  Tercer articulo en minusculas.</p>
    <p>Art\u00edculo 103 .  -  Cuarto articulo con puntuacion dispersa.</p>
</div>
</body></html>
"""
