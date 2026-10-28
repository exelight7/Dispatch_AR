"""Use the tested text-only installer with this task's verified backup and receipt."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "work/proof_20261027_pass3"))
import install_texts

install_texts.BACKUP = root / "backups/settings_english_20261028"
install_texts.RECEIPT = install_texts.BACKUP / "installation_receipt.json"
install_texts.main()
