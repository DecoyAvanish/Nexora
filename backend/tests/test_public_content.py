from backend.services.public_content import PublicContentService
class Cross:
    def get_score(self,symbol):return {"ai_score":8}
class Lab:available=False
def test_demo_is_read_only_and_architecture_has_lineage(tmp_path):
    service=PublicContentService(Cross(),Lab(),None,tmp_path);demo=service.demo();architecture=service.architecture()
    assert demo["read_only"] is True and demo["paper_trading_enabled"] is False
    assert any(node["id"]=="features" for node in architecture["nodes"]);assert architecture["sample_lineage"]["fundamental_source"].startswith("SEC")
