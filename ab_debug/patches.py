"""Monkey patch to run `jing` CLI for clearer XML validation logs."""

import logging
import os
import shutil
import subprocess
from typing import Optional

from lxml import etree

from odoo import tools
from odoo.tools import config
from odoo.tools import convert as convert_mod
from odoo.tools.convert import ConvertMode, IdRef, xml_import

_logger = logging.getLogger(__name__)


def _patched_convert_xml_import(
        env,
        module,
        xmlfile,
        idref: Optional[IdRef] = None,
        mode: ConvertMode = "init",
        noupdate=False,
        report=None,
):
    """Replicate core convert_xml_import but prefer `jing` CLI for clearer errors."""
    doc = etree.parse(xmlfile)
    schema = os.path.join(config.root_path, "import_xml.rng")
    relaxng = etree.RelaxNG(etree.parse(schema))
    try:
        relaxng.assert_(doc)
    except Exception:
        _logger.exception("The XML file '%s' does not fit the required schema!", xmlfile.name)

        jing_bin = shutil.which("jing")
        if jing_bin:
            try:
                proc = subprocess.run(
                    [jing_bin, schema, xmlfile.name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                    text=True,
                )
                if proc.stdout:
                    _logger.warning(proc.stdout.strip())
            except Exception:
                _logger.exception("Failed to run jing for detailed RNG validation")
        else:
            for e in relaxng.error_log:
                _logger.warning(e)
            _logger.info("Install 'jingtrang' (or ensure `jing` is on PATH) for more precise validation messages.")
        raise

    xml_filename = xmlfile if isinstance(xmlfile, str) else xmlfile.name
    obj = xml_import(env, module, idref, mode, noupdate=noupdate, xml_filename=xml_filename)
    obj.parse(doc.getroot())


# Apply monkey patch at import time.
tools.convert.convert_xml_import = _patched_convert_xml_import
convert_mod.convert_xml_import = _patched_convert_xml_import
