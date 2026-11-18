"""Idempotent local database schema migration entry point."""
from backend.services.paper_execution import PaperExecutionService
from backend.services.research_journal import ResearchJournalService
from backend.services.score_history import ScoreHistoryService
from backend.services.news_intelligence import NewsIntelligenceService
from backend.services.pipeline import PipelineOrchestrator
from backend.services.observability import ObservabilityService
from backend.services.production_controls import ProductionControls

class Noop:pass
def main():
    PaperExecutionService();ResearchJournalService();ScoreHistoryService();NewsIntelligenceService(Noop(),Noop());PipelineOrchestrator();ObservabilityService();ProductionControls();print("Database schemas are current.")
if __name__=="__main__":main()
