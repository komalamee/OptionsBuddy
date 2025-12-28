"""
Documentation Validation Tests for Options Buddy

This test suite ensures that all documentation is:
1. Present and complete
2. Properly structured
3. Consistent with the codebase
4. Up-to-date with required sections

Run with: pytest tests/test_docs.py -v
"""

import os
import re
from pathlib import Path
from datetime import datetime

import pytest


# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"


class TestDocumentationExists:
    """Test that all required documentation files exist."""

    def test_readme_exists(self):
        """README.md must exist in project root."""
        readme = PROJECT_ROOT / "README.md"
        assert readme.exists(), "README.md is missing from project root"

    def test_prd_exists(self):
        """PRD.md must exist in docs folder."""
        prd = DOCS_DIR / "PRD.md"
        assert prd.exists(), "docs/PRD.md is missing"

    def test_changelog_exists(self):
        """CHANGELOG.md must exist in docs folder."""
        changelog = DOCS_DIR / "CHANGELOG.md"
        assert changelog.exists(), "docs/CHANGELOG.md is missing"

    def test_tasks_exists(self):
        """TASKS.md must exist in docs folder."""
        tasks = DOCS_DIR / "TASKS.md"
        assert tasks.exists(), "docs/TASKS.md is missing"

    def test_docs_directory_exists(self):
        """docs/ directory must exist."""
        assert DOCS_DIR.exists(), "docs/ directory is missing"
        assert DOCS_DIR.is_dir(), "docs/ must be a directory"


class TestReadmeStructure:
    """Test README.md has required sections."""

    @pytest.fixture
    def readme_content(self):
        readme = PROJECT_ROOT / "README.md"
        if readme.exists():
            return readme.read_text()
        return ""

    def test_readme_has_title(self, readme_content):
        """README must have a main title."""
        assert "# Options Buddy" in readme_content, "README missing main title"

    def test_readme_has_features(self, readme_content):
        """README must have features section."""
        assert "## Features" in readme_content, "README missing Features section"

    def test_readme_has_quick_start(self, readme_content):
        """README must have quick start section."""
        assert "## Quick Start" in readme_content or "## Installation" in readme_content, \
            "README missing Quick Start/Installation section"

    def test_readme_has_architecture(self, readme_content):
        """README must have architecture section."""
        assert "## Architecture" in readme_content or "## Project Structure" in readme_content, \
            "README missing Architecture section"

    def test_readme_has_documentation_links(self, readme_content):
        """README must link to other docs."""
        assert "docs/PRD.md" in readme_content, "README missing link to PRD"
        assert "docs/CHANGELOG.md" in readme_content, "README missing link to CHANGELOG"
        assert "docs/TASKS.md" in readme_content, "README missing link to TASKS"


class TestPRDStructure:
    """Test PRD.md has required sections."""

    @pytest.fixture
    def prd_content(self):
        prd = DOCS_DIR / "PRD.md"
        if prd.exists():
            return prd.read_text()
        return ""

    def test_prd_has_title(self, prd_content):
        """PRD must have a title."""
        assert "# Options Buddy" in prd_content or "# Product Requirements" in prd_content, \
            "PRD missing title"

    def test_prd_has_executive_summary(self, prd_content):
        """PRD must have executive summary."""
        assert "## Executive Summary" in prd_content or "## Summary" in prd_content, \
            "PRD missing Executive Summary"

    def test_prd_has_problem_statement(self, prd_content):
        """PRD must have problem statement."""
        assert "## Problem Statement" in prd_content or "Problem" in prd_content, \
            "PRD missing Problem Statement"

    def test_prd_has_functional_requirements(self, prd_content):
        """PRD must have functional requirements."""
        assert "## Functional Requirements" in prd_content or "### FR-" in prd_content, \
            "PRD missing Functional Requirements"

    def test_prd_has_non_functional_requirements(self, prd_content):
        """PRD must have non-functional requirements."""
        assert "## Non-Functional Requirements" in prd_content or "### NFR-" in prd_content, \
            "PRD missing Non-Functional Requirements"

    def test_prd_has_technical_architecture(self, prd_content):
        """PRD must have technical architecture section."""
        assert "## Technical Architecture" in prd_content or "## Architecture" in prd_content, \
            "PRD missing Technical Architecture"

    def test_prd_has_version_info(self, prd_content):
        """PRD must have version information."""
        assert "Version:" in prd_content or "**Version:**" in prd_content, \
            "PRD missing version information"

    def test_prd_requirements_have_status(self, prd_content):
        """PRD requirements should have status indicators."""
        # Check for status column in tables
        assert "Status" in prd_content, "PRD requirements missing status tracking"
        # Check for actual status values
        assert "Done" in prd_content or "Completed" in prd_content, \
            "PRD has no completed requirements marked"


class TestChangelogStructure:
    """Test CHANGELOG.md follows Keep a Changelog format."""

    @pytest.fixture
    def changelog_content(self):
        changelog = DOCS_DIR / "CHANGELOG.md"
        if changelog.exists():
            return changelog.read_text()
        return ""

    def test_changelog_has_title(self, changelog_content):
        """CHANGELOG must have a title."""
        assert "# Changelog" in changelog_content, "CHANGELOG missing title"

    def test_changelog_has_format_reference(self, changelog_content):
        """CHANGELOG should reference Keep a Changelog format."""
        assert "Keep a Changelog" in changelog_content, \
            "CHANGELOG should reference Keep a Changelog format"

    def test_changelog_has_semver_reference(self, changelog_content):
        """CHANGELOG should reference Semantic Versioning."""
        assert "Semantic Versioning" in changelog_content, \
            "CHANGELOG should reference Semantic Versioning"

    def test_changelog_has_unreleased_section(self, changelog_content):
        """CHANGELOG should have Unreleased section."""
        assert "## [Unreleased]" in changelog_content, \
            "CHANGELOG missing [Unreleased] section"

    def test_changelog_has_version_entries(self, changelog_content):
        """CHANGELOG must have at least one version entry."""
        # Look for version pattern like [1.0.0] - 2024-12-28
        version_pattern = r'\[[\d]+\.[\d]+\.[\d]+\]'
        matches = re.findall(version_pattern, changelog_content)
        assert len(matches) >= 1, "CHANGELOG must have at least one version entry"

    def test_changelog_has_added_section(self, changelog_content):
        """CHANGELOG should have Added section."""
        assert "### Added" in changelog_content, "CHANGELOG missing Added section"

    def test_changelog_versions_are_dated(self, changelog_content):
        """CHANGELOG versions should have dates."""
        # Pattern: [x.x.x] - YYYY-MM-DD
        date_pattern = r'\[[\d]+\.[\d]+\.[\d]+\] - \d{4}-\d{2}-\d{2}'
        matches = re.findall(date_pattern, changelog_content)
        assert len(matches) >= 1, "CHANGELOG versions must have dates in YYYY-MM-DD format"


class TestTasksStructure:
    """Test TASKS.md has required sections for task tracking."""

    @pytest.fixture
    def tasks_content(self):
        tasks = DOCS_DIR / "TASKS.md"
        if tasks.exists():
            return tasks.read_text()
        return ""

    def test_tasks_has_title(self, tasks_content):
        """TASKS must have a title."""
        assert "# Options Buddy - Task Tracking" in tasks_content or "# Task" in tasks_content, \
            "TASKS missing title"

    def test_tasks_has_last_updated(self, tasks_content):
        """TASKS must have last updated date."""
        assert "Last Updated:" in tasks_content or "**Last Updated:**" in tasks_content, \
            "TASKS missing Last Updated date"

    def test_tasks_has_status_legend(self, tasks_content):
        """TASKS must have status legend."""
        assert "Status" in tasks_content and "Legend" in tasks_content or \
               ("Done" in tasks_content and "In Progress" in tasks_content and "Todo" in tasks_content), \
            "TASKS missing status legend"

    def test_tasks_has_version_sections(self, tasks_content):
        """TASKS should have version-based sections."""
        assert "## V1" in tasks_content or "## Version 1" in tasks_content, \
            "TASKS missing version sections"

    def test_tasks_has_completed_tasks(self, tasks_content):
        """TASKS should have some completed tasks marked."""
        # Check for done indicators
        done_indicators = [":white_check_mark:", "Done", "[x]", "Completed"]
        has_done = any(indicator in tasks_content for indicator in done_indicators)
        assert has_done, "TASKS should have some completed tasks marked"

    def test_tasks_has_session_log(self, tasks_content):
        """TASKS should have session log for continuity."""
        assert "## Session Log" in tasks_content or "Session" in tasks_content, \
            "TASKS should have session log for pickup continuity"

    def test_tasks_has_quick_stats(self, tasks_content):
        """TASKS should have quick stats section."""
        assert "## Quick Stats" in tasks_content or "Stats" in tasks_content or "Completion" in tasks_content, \
            "TASKS should have quick stats or completion tracking"


class TestDocumentationConsistency:
    """Test that documentation is consistent across files."""

    @pytest.fixture
    def all_docs(self):
        docs = {}
        for filename in ["README.md", "docs/PRD.md", "docs/CHANGELOG.md", "docs/TASKS.md"]:
            filepath = PROJECT_ROOT / filename
            if filepath.exists():
                docs[filename] = filepath.read_text()
            else:
                docs[filename] = ""
        return docs

    def test_version_consistency(self, all_docs):
        """Version numbers should be consistent across docs."""
        # Extract version from README
        readme = all_docs.get("README.md", "")
        prd = all_docs.get("docs/PRD.md", "")
        changelog = all_docs.get("docs/CHANGELOG.md", "")

        # Check that 1.0.0 appears in all docs (current version)
        assert "1.0.0" in readme, "README missing version 1.0.0"
        assert "1.0.0" in prd, "PRD missing version 1.0.0"
        assert "1.0.0" in changelog, "CHANGELOG missing version 1.0.0"

    def test_project_name_consistency(self, all_docs):
        """Project name should be consistent across docs."""
        for filename, content in all_docs.items():
            if content:
                assert "Options Buddy" in content, f"{filename} missing project name 'Options Buddy'"


class TestCodebaseDocumentationSync:
    """Test that documentation reflects actual codebase structure."""

    def test_documented_directories_exist(self):
        """Directories mentioned in docs should exist."""
        expected_dirs = ["config", "core", "data", "database", "pages"]
        for dir_name in expected_dirs:
            dir_path = PROJECT_ROOT / dir_name
            assert dir_path.exists(), f"Documented directory '{dir_name}' does not exist"

    def test_documented_files_exist(self):
        """Key files mentioned in docs should exist."""
        expected_files = [
            "app.py",
            "requirements.txt",
            ".env.example",
            "config/constants.py",
            "config/settings.py",
            "core/black_scholes.py",
            "core/volatility.py",
            "core/mispricing.py",
            "core/scoring.py",
            "data/ibkr_client.py",
            "data/option_chain.py",
            "data/historical_data.py",
            "database/models.py",
            "database/db_manager.py",
        ]
        for file_path in expected_files:
            full_path = PROJECT_ROOT / file_path
            assert full_path.exists(), f"Documented file '{file_path}' does not exist"

    def test_streamlit_pages_exist(self):
        """Streamlit pages mentioned in docs should exist."""
        pages_dir = PROJECT_ROOT / "pages"
        expected_pages = [
            "1_dashboard.py",
            "2_scanner.py",
            "3_analyzer.py",
            "4_positions.py",
            "5_suggestions.py",
            "6_settings.py",
        ]
        for page in expected_pages:
            page_path = pages_dir / page
            assert page_path.exists(), f"Documented page '{page}' does not exist"


class TestDocumentationQuality:
    """Test documentation quality metrics."""

    @pytest.fixture
    def all_docs(self):
        docs = {}
        for filename in ["README.md", "docs/PRD.md", "docs/CHANGELOG.md", "docs/TASKS.md"]:
            filepath = PROJECT_ROOT / filename
            if filepath.exists():
                docs[filename] = filepath.read_text()
            else:
                docs[filename] = ""
        return docs

    def test_readme_minimum_length(self, all_docs):
        """README should have substantial content."""
        readme = all_docs.get("README.md", "")
        assert len(readme) >= 1000, "README should be at least 1000 characters"

    def test_prd_minimum_length(self, all_docs):
        """PRD should be comprehensive."""
        prd = all_docs.get("docs/PRD.md", "")
        assert len(prd) >= 5000, "PRD should be at least 5000 characters"

    def test_changelog_minimum_length(self, all_docs):
        """CHANGELOG should have substantial entries."""
        changelog = all_docs.get("docs/CHANGELOG.md", "")
        assert len(changelog) >= 2000, "CHANGELOG should be at least 2000 characters"

    def test_tasks_minimum_length(self, all_docs):
        """TASKS should have comprehensive tracking."""
        tasks = all_docs.get("docs/TASKS.md", "")
        assert len(tasks) >= 3000, "TASKS should be at least 3000 characters"

    def test_no_todo_placeholders(self, all_docs):
        """Docs should not have TODO placeholders."""
        for filename, content in all_docs.items():
            # Allow "Todo" as a status but not "TODO:" or "TODO -" as placeholders
            placeholder_patterns = ["TODO:", "TODO -", "FIXME:", "XXX:"]
            for pattern in placeholder_patterns:
                assert pattern not in content, f"{filename} contains placeholder '{pattern}'"

    def test_no_broken_links(self, all_docs):
        """Check for obviously broken internal links."""
        readme = all_docs.get("README.md", "")
        # Check that linked docs exist
        if "docs/PRD.md" in readme:
            assert (PROJECT_ROOT / "docs/PRD.md").exists(), "README links to missing PRD.md"
        if "docs/CHANGELOG.md" in readme:
            assert (PROJECT_ROOT / "docs/CHANGELOG.md").exists(), "README links to missing CHANGELOG.md"
        if "docs/TASKS.md" in readme:
            assert (PROJECT_ROOT / "docs/TASKS.md").exists(), "README links to missing TASKS.md"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
