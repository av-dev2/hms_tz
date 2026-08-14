# Copyright (c) 2025, Aakvatech and Contributors
# See license.txt
import inspect
import uuid
from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase
from pypdf import PdfWriter

from hms_tz.jubilee.doctype.jubilee_patient_claim.jubilee_patient_claim import read_multi_pdf


class TestClaimPdf(FrappeTestCase):
    def test_pdf_is_serialised_in_memory(self):
        """Claim PDFs carry patient data and must not land in a shared temp dir."""
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)

        with patch("builtins.open") as mocked_open:
            filedata = read_multi_pdf(writer)

        mocked_open.assert_not_called()
        self.assertIsInstance(filedata, bytes)
        self.assertTrue(filedata.startswith(b"%PDF"))


class TestFolioId(FrappeTestCase):
    def claim_source(self):
        from hms_tz.jubilee.doctype.jubilee_patient_claim import jubilee_patient_claim

        return inspect.getsource(jubilee_patient_claim)

    def test_folio_id_does_not_use_uuid1(self):
        """uuid1 leaks the host MAC address and is predictable from its timestamp."""
        self.assertNotIn("uuid.uuid1(", self.claim_source())

    def test_folio_id_is_a_uuid4_string(self):
        """FolioID goes out to Jubilee, so it must serialise as a plain string."""
        self.assertIn('self.folio_id = str(uuid.uuid4())', self.claim_source())

        folio_id = str(uuid.uuid4())
        self.assertIsInstance(folio_id, str)
        self.assertEqual(uuid.UUID(folio_id).version, 4)
