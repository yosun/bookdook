import os
import zipfile
import uuid
from datetime import datetime


def write_minimal_epub(path: str, title: str, author: str, language: str, chapters: list[tuple[str, str]]):
    """Create a minimal EPUB 3 file with provided chapters.

    chapters: list of (filename_slug, html_body_without_tags)
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    book_id = str(uuid.uuid4())
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    with zipfile.ZipFile(path, "w") as zf:
        # Required mimetype first, uncompressed
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        # Container
        zf.writestr(
            "META-INF/container.xml",
            """
<?xml version='1.0' encoding='utf-8'?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
  </container>
""".strip(),
        )

        # nav document
        nav_items = "\n".join(
            f"<li><a href='{slug}.xhtml'>{i+1}. {slug.title()}</a></li>" for i, (slug, _) in enumerate(chapters)
        )
        nav = f"""
<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head><title>Navigation</title></head>
  <body>
    <nav epub:type="toc" id="toc">
      <ol>
        {nav_items}
      </ol>
    </nav>
  </body>
 </html>
""".strip()
        zf.writestr("OEBPS/nav.xhtml", nav)

        # content files
        manifest_items = [
            "<item id='nav' href='nav.xhtml' properties='nav' media-type='application/xhtml+xml'/>"
        ]
        spine_items = []
        for i, (slug, body) in enumerate(chapters):
            html = f"""
<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta charset="utf-8" />
    <title>{title} - {slug.title()}</title>
  </head>
  <body>
    <h1>{slug.title()}</h1>
    <p>{body}</p>
  </body>
 </html>
""".strip()
            href = f"{slug}.xhtml"
            zf.writestr(f"OEBPS/{href}", html)
            manifest_items.append(
                f"<item id='c{i}' href='{href}' media-type='application/xhtml+xml'/>"
            )
            spine_items.append(f"<itemref idref='c{i}'/>")

        manifest = "\n      ".join(manifest_items)
        spine = "\n      ".join(spine_items)
        content_opf = f"""
<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0" xml:lang="{language}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:uuid:{book_id}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:language>{language}</dc:language>
    <dc:creator>{author}</dc:creator>
    <meta property="dcterms:modified">{now}</meta>
  </metadata>
  <manifest>
      {manifest}
  </manifest>
  <spine>
      {spine}
  </spine>
 </package>
""".strip()
        zf.writestr("OEBPS/content.opf", content_opf)

