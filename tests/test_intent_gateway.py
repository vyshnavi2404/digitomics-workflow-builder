from app.agents.intent_gateway import IntentGateway
from app.domain.models import IntentType


def test_general_dbms_question_is_out_of_scope():
    gateway = IntentGateway()

    result = gateway.classify("What is normalization in DBMS?")

    assert result.intent == IntentType.OUT_OF_SCOPE


def test_java_question_is_out_of_scope():
    gateway = IntentGateway()

    result = gateway.classify("Explain polymorphism in Java.")

    assert result.intent == IntentType.OUT_OF_SCOPE


def test_cnn_question_is_out_of_scope():
    gateway = IntentGateway()

    result = gateway.classify("What is the difference between CNN and RNN?")

    assert result.intent == IntentType.OUT_OF_SCOPE


def test_database_notification_is_workflow_request():
    gateway = IntentGateway()

    result = gateway.classify(
        "Whenever a new customer record is added to my database, "
        "send a notification to the sales team."
    )

    assert result.intent == IntentType.WORKFLOW_REQUEST


def test_workflow_update_is_detected():
    gateway = IntentGateway()

    result = gateway.classify(
        "Actually, send the notification to email instead."
        ,
        workflow_exists=True,
    )

    assert result.intent == IntentType.WORKFLOW_UPDATE

def test_workflow_selection_followup_is_treated_as_workflow_request():
    gateway = IntentGateway()

    result = gateway.classify(
        "email",
        workflow_selection_pending=True,
    )

    assert result.intent == IntentType.WORKFLOW_REQUEST