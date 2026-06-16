import main as app_main


def test_lookup_crud(db_session):
    s = app_main.build_services(db_session)

    cat = s["quality"].create_category("تصنيف معيار", "وصف")
    assert cat.id is not None
    assert len(s["quality"].get_all_categories()) == 1
    assert s["quality"].delete_category(cat.id) is True

    dcat = s["document"].create_category("تصنيف وثيقة")
    assert dcat.id is not None
    assert s["document"].delete_category(dcat.id) is True

    pos = s["hr"].create_position("منصب اختبار", "وصف")
    assert pos.id is not None and pos.title == "منصب اختبار"
    assert s["hr"].delete_position(pos.id) is True

    rt = s["record"].add_record_type("نوع سجل")
    assert rt.id is not None
    assert s["record"].delete_record_type(rt.id) is True


def test_lookup_update(db_session):
    """Every lookup type can be edited (powers the Lookups page row-edit)."""
    s = app_main.build_services(db_session)

    cat = s["quality"].create_category("قديم", "و1")
    s["quality"].update_category(cat.id, "جديد", "و2")
    updated = s["quality"].get_all_categories()[0]
    assert updated.name == "جديد" and updated.description == "و2"

    dcat = s["document"].create_category("قديم")
    s["document"].update_category(dcat.id, "جديد", "وصف")
    assert s["document"].get_categories()[0].name == "جديد"

    rt = s["record"].add_record_type("قديم")
    s["record"].update_record_type(rt.id, "جديد", "وصف")
    assert s["record"].get_all_record_types()[0].name == "جديد"

    pos = s["hr"].create_position("قديم")
    s["hr"].update_position(pos.id, "جديد", "وصف")
    assert s["hr"].get_all_positions()[0].title == "جديد"
