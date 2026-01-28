"""
Simple SML implementation according to: https://docs.peppol.eu/edelivery/sml/Peppol-EDN-Service-Metadata-Locator-1.3.0-2025-02-06.pdf
"""

import base64
import hashlib

import dns
import dns.resolver

import requests

import xmltodict

import logging

logger  = logging.getLogger()

def check(id, include_details=False,
          sml_host="edelivery.tech.ec.europa.eu",
          id_scheme="iso6523-actorid-upis"):
  """
  Checks a participant via de DNS-based look up system (SML)
  """
  # compile NAPTR domain name: base32 of sha256 of id, lowercase without "="
  hash = hashlib.sha256()
  hash.update(id.encode())
  key = base64.b32encode(hash.digest()).lower().decode().replace("=", "")
  url = f"{key}.{id_scheme}.{sml_host}"
  logger.debug(f"DNS NAPTR domain: '{url}'")

  resolver = dns.resolver.Resolver()
  try:
    # resolve NAPTR domain
    result = resolver.resolve(url, rdtype=dns.rdatatype.NAPTR)
    # <sep> <search for> <sep> <replacement> </sep>
    #                          ^^^  host ^^^
    logger.debug(f"NAPTR record: {result[0]}")
    regexp = result[0].regexp.decode()
    host   = regexp.split(regexp[0])[2]

    # query the PCAP
    url = f"{host}/{id_scheme}::{id}"
    logger.debug(f"Service query URL: '{url}'")
    services = xmltodict.parse(requests.get(url).text)

    # services
    if include_details:
      references = services["ns3:ServiceGroup"]["ns3:ServiceMetadataReferenceCollection"]["ns3:ServiceMetadataReference"]
      for index, ref in enumerate(references):
        s = requests.get(ref["@href"])
        service = xmltodict.parse(s.text)
        references[index] = service
    return services
  except Exception as ex:
    raise ValueError(f"can't resolve '{id}': {ex}")

# expose cli enabled functions
cli = { "check" : check }
