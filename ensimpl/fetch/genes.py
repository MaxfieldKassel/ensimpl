# -*- coding: utf_8 -*-
import sqlite3

import ensimpl.utils as utils
import ensimpl.fetch.utils as fetch_utils

LOG = utils.get_logger()


SQL_ID_FULL = '''
SELECT e.ensembl_id gene_id,
       e.ensembl_version gene_version,
       e.species_id gene_species_id,
       e.symbol gene_symbol,
       e.name gene_name,
       e.synonyms gene_synonyms,
       e.external_ids gene_external_ids,
       e.chromosome gene_chromosome,
       e.start_position gene_start,
       e.end_position gene_end,
       e.strand gene_strand,
       g.*
  FROM ensembl_genes e,
       ensembl_gtpe g
 WHERE e.ensembl_id = g.gene_id
'''

SQL_ID_GENES = '''
SELECT e.ensembl_id ensembl_id, 
       e.ensembl_id gene_id,
       e.ensembl_version gene_version,
       e.species_id gene_species_id,
       e.symbol gene_symbol,
       e.name gene_name,
       e.synonyms gene_synonyms,
       e.external_ids gene_external_ids,
       e.chromosome gene_chromosome,
       e.start_position gene_start,
       e.end_position gene_end,
       e.strand gene_strand,
       'EG' type_key
  FROM ensembl_genes e
 WHERE 1 = 1
'''

SQL_WHERE_ID = '''
  AND e.ensembl_id IN (SELECT distinct ensembl_id FROM {})
'''

SQL_WHERE_REGION = '''
   AND e.chromosome = :chromosome
   AND e.start_position <= :end_position
   AND e.end_position >= :start_position
'''

SQL_ORDER_BY_ID = ' ORDER BY e.ensembl_id'

SQL_ORDER_BY_POSITION = '''
 ORDER BY cast(
       replace(replace(replace(e.chromosome,'X','50'),'Y','51'),'MT','51') 
       AS int), e.start_position, e.end_position
'''


def get(version, species, ids=None, region=None, order='id', full=False):
    """Get genes matching the ids.

        Each match object will contain:

        =================  =======  ============================================
        Element            Type     Description
        =================  =======  ============================================
        ensembl_id         string   Ensembl gene identifier
        ensembl_version    integer  version of the identifier
        species_id         string   species identifier: 'Mm', 'Hs', etc
        chromosome         string   the chromosome
        start              integer  start position in base pairs
        end                integer  end position in base pairs
        strand             string   '+' or '-'
        gene_name          string   name of the gene
        gene_symbol        string   gene symbol
        gene_synonyms      list     list of strings
        gene_external_ids  list     each having keys of 'db' and 'db_id
        =================  =======  ============================================

        If ``full`` is ``True``, each match will also contain the following:

        ``transcripts``, with each item containing:

        =================  =======  ============================================
        Element            Type     Description
        =================  =======  ============================================
        id                 string   Ensembl gene identifier
        ensembl_version    integer  version of the identifier
        symbol             string   transcript symbol
        start              integer  start position in base pairs
        end                integer  end position in base pairs
        exons              list     dict of: number,id,start,end,ensembl_version
        protein            dict     id, start, end, ensembl_version
        =================  =======  ============================================

    Args:
        version (int): The Ensembl version number.
        species (str): The Ensembl species identifier.
        ids (list): A ``list`` of ``str`` which are Ensembl identifiers.
        full (bool): True to retrieve all information including transcripts,
            exons, proteins.  False will only retrieve the top level gene
            information.

    Returns:
        list: A ``list`` of ``dicts`` representing genes.

    Raises:
        Exception: When sqlite error or other error occurs.
    """
    results = {}

    try:
        conn = fetch_utils.connect_to_database(version, species)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        temp_table = 'lookup_ids_{}'.format(utils.create_random_string())

        SQL_QUERY = SQL_ID_GENES
        variables = {}

        if full:
            # genes, transcripts, proteins, exons
            SQL_QUERY = SQL_ID_FULL

        if ids:
            # create a temp table and insert into
            SQL_TEMP = ('CREATE TEMPORARY TABLE {} ( '
                        'ensembl_id TEXT, '
                        'PRIMARY KEY (ensembl_id) '
                        ');').format(temp_table)

            cursor.execute(SQL_TEMP)

            SQL_TEMP = 'INSERT INTO {} VALUES (?);'.format(temp_table)
            ids = [(_,) for _ in ids]
            cursor.executemany(SQL_TEMP, ids)

            SQL_QUERY = '{} {}'.format(SQL_QUERY,
                                       SQL_WHERE_ID.format(temp_table))

        if region:
            if isinstance(region, str):
                region = fetch_utils.str_to_region(region)

            SQL_QUERY = '{} {}'.format(SQL_QUERY, SQL_WHERE_REGION)
            variables['chromosome'] = region.chromosome
            variables['start_position'] = region.start_position
            variables['end_position'] = region.end_position

        if order and order.lower() == 'position':
            SQL_QUERY = '{} {}'.format(SQL_QUERY,
                                       SQL_ORDER_BY_POSITION)
        else:
            SQL_QUERY = '{} {}'.format(SQL_QUERY,
                                       SQL_ORDER_BY_ID)

        for row in cursor.execute(SQL_QUERY, variables):
            gene_id = row['gene_id']
            ensembl_id = row['ensembl_id']

            gene = results.get(gene_id)

            if not gene:
                gene = {'id': gene_id, 'transcripts': {}}

            if row['type_key'] == 'EG':
                gene['species_id'] = row['gene_species_id']
                gene['chromosome'] = row['gene_chromosome']
                gene['start'] = row['gene_start']
                gene['end'] = row['gene_end']
                gene['strand'] = '+' if row['gene_strand'] > 0 else '-'

                if row['gene_version']:
                    gene['ensembl_version'] = row['gene_version']

                if row['gene_symbol']:
                    gene['symbol'] = row['gene_symbol']

                if row['gene_name']:
                    gene['name'] = row['gene_name']

                if row['gene_synonyms']:
                    row_synonyms = row['gene_synonyms']
                    gene['synonyms'] = row_synonyms.split('||')

                if row['gene_external_ids']:
                    row_external_ids = row['gene_external_ids']
                    external_ids = []
                    if row_external_ids:
                        tmp_external_ids = row_external_ids.split('||')
                        for e in tmp_external_ids:
                            elem = e.split('/')
                            external_ids.append({'db': elem[0], 'db_id': elem[1]})
                    gene['external_ids'] = external_ids

            elif row['type_key'] == 'ET':
                transcript_id = row['transcript_id']
                transcript = {'id': transcript_id, 'exons': {}}

                if row['ensembl_id_version']:
                    transcript['ensembl_version'] = row['ensembl_id_version']

                if row['ensembl_symbol']:
                    transcript['symbol'] = row['ensembl_symbol']

                transcript['start'] = row['start']
                transcript['end'] = row['end']

                gene['transcripts'][transcript_id] = transcript

            elif row['type_key'] == 'EE':
                transcript_id = row['transcript_id']
                transcript = gene['transcripts'].get(transcript_id,
                                                     {'id': transcript_id,
                                                      'exons': {}})

                exon = {'id': ensembl_id,
                        'start': row['start'],
                        'end': row['end'],
                        'number': row['exon_number']}

                if row['ensembl_id_version']:
                    exon['ensembl_version'] = row['ensembl_id_version']

                transcript['exons'][ensembl_id] = exon

                gene['transcripts'][transcript_id] = transcript

            elif row['type_key'] == 'EP':
                transcript_id = row['transcript_id']
                transcript = gene['transcripts'].get(transcript_id,
                                                     {'id': transcript_id,
                                                      'exons': {}})

                transcript['protein'] = {'id': ensembl_id,
                                         'start': row['start'],
                                         'end': row['end']}

                if row['ensembl_id_version']:
                    transcript['protein']['ensembl_version'] = row['ensembl_id_version']

                gene['transcripts'][transcript_id] = transcript
            else:
                LOG.error('Unknown')

            results[gene_id] = gene

        cursor.close()

        if full:
            # convert transcripts, etc to sorted list rather than dict
            ret = {}
            for (gene_id, gene) in results.items():
                if gene:
                    t = []
                    for (transcript_id, transcript) in gene['transcripts'].items():
                        e = []
                        for (exon_id, exon) in transcript['exons'].items():
                            e.append(exon)
                        transcript['exons'] = sorted(e, key=lambda ex: ex['number'])
                        t.append(transcript)
                    gene['transcripts'] = sorted(t, key=lambda tr: tr['start'])
                ret[gene_id] = gene

            results = ret
        else:
            ret = {}
            for (gene_id, gene) in results.items():
                if gene:
                    del gene['transcripts']
                ret[gene_id] = gene

            results = ret

        cursor.close()
        conn.close()

    except sqlite3.Error as e:
        raise Exception(e)

    return results






