import pytest
from unittest.mock import Mock, patch

from knowledge.tasks import process_document_task


@pytest.mark.django_db
def test_process_document_task_delegates_to_processing():
    processing_result = "processed text"

    with patch(
        "knowledge.tasks.process_document",
        return_value=processing_result,
    ) as mock_process:
        result = process_document_task(123)

    mock_process.assert_called_once_with(123)
    assert result == processing_result