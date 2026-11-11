from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGlobalSearch(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.GlobalSearch = cls.env["global.search"]
        cls.partner = cls.env["res.partner"].create({
            "name": "Waterman",
            "ref": "WM-0042",
        })

    def test_name_match(self):
        group = self.GlobalSearch._search_model("res.partner", "water", 5)
        self.assertTrue(group)
        self.assertEqual(group["model"], "res.partner")
        self.assertIn(self.partner.id, [rec["id"] for rec in group["records"]])

    def test_no_match(self):
        self.assertFalse(self.GlobalSearch._search_model("res.partner", "zzzqqq", 5))

    def test_limit_sets_has_more(self):
        for i in range(3):
            self.env["res.partner"].create({"name": "Watertown %s" % i})
        group = self.GlobalSearch._search_model("res.partner", "water", 2)
        self.assertEqual(len(group["records"]), 2)
        self.assertTrue(group["has_more"])

    def test_extra_field(self):
        ref_field = self.env["ir.model.fields"]._get("res.partner", "ref")
        config = self.env["global.search.config"].create({
            "model_id": self.env["ir.model"]._get("res.partner").id,
            "extra_field_ids": [(6, 0, ref_field.ids)],
        })
        group = self.GlobalSearch._search_model("res.partner", "WM-0042", 5, config)
        self.assertTrue(group)

    def test_short_term_returns_nothing(self):
        result = self.GlobalSearch.search_records("wa")
        self.assertEqual(result, {"groups": [], "has_next": False})
