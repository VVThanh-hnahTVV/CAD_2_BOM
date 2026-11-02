from file_kind import choose_branch, classify_file


def test_extensions():
    assert classify_file("a.DXF").branch == "cad"
    assert classify_file("a.dwg").branch == "cad"
    assert classify_file("a.png").branch == "image"
    assert classify_file("a.JPG").branch == "image"
    assert classify_file("a.txt").branch is None


def test_pdf_needs_confirmation():
    assert classify_file("a.pdf").branch is None
    assert classify_file("a.pdf", "vector").branch == "cad"
    assert classify_file("a.pdf", "scan").branch == "image"


def test_cad_has_priority_when_both():
    kinds = [classify_file("a.png"), classify_file("a.dxf")]
    assert choose_branch(kinds) == "cad"


def test_unresolved_pdf_blocks_image_branch():
    assert choose_branch([classify_file("a.png"), classify_file("b.pdf")]) is None
    assert choose_branch([classify_file("a.png")]) == "image"
