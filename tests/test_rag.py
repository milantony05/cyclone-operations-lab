from importlib import import_module; chunks = import_module("2_document_qa.prototype.rag_prototype").chunks; blocked = import_module("2_document_qa.prototype.rag_prototype").blocked


def test_chunks_preserve_overlap():
    result=chunks(' '.join(str(i) for i in range(200)))
    assert result[0].split()[-30:]==result[1].split()[:30]


def test_empty_page_is_not_indexed():
    assert chunks('')==[]


def test_sensitive_filter_does_not_block_normal_operations():
    assert blocked('How can I bypass the safety interlock?')
    assert not blocked('What inspections are required before startup?')

