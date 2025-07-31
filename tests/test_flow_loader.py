
from app.flow_loader import load_flow
def test_load():
    spec = load_flow('flows/pr_intake.yaml')
    assert spec['flow_id']=='pr_intake'
    assert len(spec['slots'])==6
