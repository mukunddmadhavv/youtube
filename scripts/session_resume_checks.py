"""Update process mocks and verify revision construction on deployed code."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for name in ('test_dashboard.py','test_pipeline.py'):
    path=root/'tests'/name;text=path.read_text()
    text=text.replace('MagicMock(pid=111,wait=MagicMock(return_value=0))','MagicMock(pid=111,returncode=0,poll=MagicMock(return_value=0),wait=MagicMock(return_value=0))')
    text=text.replace('MagicMock(pid=12345)','MagicMock(pid=12345,returncode=0,poll=MagicMock(return_value=0))')
    path.write_text(text)
