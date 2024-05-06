"""
Opex Manifest Generator tool

This tool is utilised to recusrively generate Opex files for files / directories for use in uploading to Preservica and other OPEX conformin systems.

author: Christopher Prince
license: Apache License 2.0"
"""

import lxml.etree as ET
import os
from auto_classification_generator import ClassificationGenerator
from auto_classification_generator.common import export_list_txt, export_xl, export_csv, define_output_file
from datetime import datetime
import time
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype
from opex_manifest_generator.hash import HashGenerator
from opex_manifest_generator.common import *
import stat
import shutil

class OpexManifestGenerator():
    def __init__(self,
                 root: str,
                 output_path: os.path = os.getcwd(),
                 meta_dir_flag: bool = True,
                 metadata_dir: bool = os.path.join(os.path.dirname(os.path.realpath(__file__)), "metadata"),
                 metadata_flag: str = 'none',
                 autoclass_flag: str = None,
                 prefix: str = None,
                 acc_prefix: str = None,
                 startref: int = 1,
                 algorithm: str = None,
                 empty_flag: bool = False,
                 remove_flag: bool = False,
                 clear_opex_flag: bool = False,
                 export_flag: bool = False,
                 input: str = None,
                 zip_flag: bool = False,
                 hidden_flag: bool = False,
                 output_format: str = "xlsx",
                 print_xmls_flag: bool = False):
        
        self.root = os.path.abspath(root)
        self.opexns = "http://www.openpreservationexchange.org/opex/v1.2"        
        self.list_path = []
        self.list_fixity = []
        self.start_time = datetime.now()
        self.algorithm = algorithm
        self.empty_flag = empty_flag
        self.remove_flag = remove_flag
        self.export_flag = export_flag
        self.startref = startref
        self.autoclass_flag = autoclass_flag
        self.output_path = output_path
        self.clear_opex_flag = clear_opex_flag
        self.meta_dir_flag = meta_dir_flag
        self.prefix = prefix
        self.acc_prefix = acc_prefix
        self.input = input
        self.title_flag = False
        self.description_flag = False
        self.security_flag = False
        self.ignore_flag = False
        self.sourceid_flag = False
        self.hash_from_spread = False        
        self.hidden_flag = hidden_flag
        self.zip_flag = zip_flag
        self.output_format = output_format
        self.metadata_flag = metadata_flag
        self.metadata_dir = metadata_dir
        self.print_xmls_flag = print_xmls_flag
        
    def print_running_time(self):
        print(f'Running time: {datetime.now() - self.start_time}')
        time.sleep(1)
    
    def index_df_lookup(self, path: str):
        idx = self.df['FullName'].index[self.df['FullName'] == path]
        return idx

    def meta_df_lookup(self, idx: pd.Index):
        try:
            if idx.empty:
                title = None
                description = None
                security = None
            else:
                    if self.title_flag:
                        title = self.df['Title'].loc[idx].item()
                        if str(title).lower() in {"nan","nat"}:
                            title = None
                    else:
                        title = None
                    if self.description_flag:
                        description = self.df['Description'].loc[idx].item()
                        if str(description).lower() in {"nan","nat"}:
                            description = None
                    else:
                        description = None
                    if self.security_flag:
                        security = self.df['Security'].loc[idx].item()
                        if str(security).lower() in {"nan","nat"}:
                            security = None
                    else:
                        security = None
            return title,description,security
        except Exception as e:
            print('Error Looking up XIP Metadata')
            print(e)
    
    def remove_df_lookup(self, path: str, idx: pd.Index):
        try:
            if idx.empty:
                return False
            else:
                remove = self.df['Removals'].loc[idx].item()
                if str(remove).lower() in {"nan","nat"}:
                    return False
                elif bool(remove):
                    print(f"Removing: {path}")
                    # Not functioning correctly
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    return True
                else:
                    return False
        except Exception as e:
            print('Error looking up Removals')
            print(e)
                
    def ignore_df_lookup(self, idx: pd.Index):
        try:
            if idx.empty:
                return False
            else:
                ignore = self.df['Ignore'].loc[idx].item()
            if str(ignore).lower() in {"nan","nat"}:
                return False
            elif str(ignore).lower() in {"true", "1.0"}:
                return True
            elif str(ignore).lower() in {"false", "0.0"}:
                return False
        except Exception as e:
            print('Error looking up Removals')
            print(e)

    def sourceid_df_lookup(self, xml_element: ET.SubElement, idx: pd.Index):
        try:
            if idx.empty:
                pass
            else:
                sourceid = self.df['SourceID'].loc[idx].item()
                if str(sourceid) in {"nan","nat"}:
                    pass
                else:
                    source_xml = ET.SubElement(xml_element,f"{{{self.opexns}}}SourceID")
                    source_xml.text = str(sourceid)
        except Exception as e:
            print('Error looking up SourceID')
            print(e)

    def hash_df_lookup(self, file_path: str, xml_fixities: ET.SubElement, idx: pd.Index):
        try:
            if idx.empty:
                pass
            else:
                if "Hash" in self.column_headers and "Algorithm" in self.column_headers:
                    self.fixity = ET.SubElement(xml_fixities,f"{{{self.opexns}}}Fixity")        
                    self.hash = self.df["Hash"].loc[idx].item()
                    self.algorithm = self.df["Algorithm"].loc[idx].item()
                    self.hash = HashGenerator(algorithm=self.algorithm).hash_generator(file_path)
                    self.fixity.set("type", self.algorithm)
                    self.fixity.set("value",self.hash)
        except Exception as e:
            print('Error looking up Removals')
            print(e)

    def ident_df_lookup(self, idx: pd.Index, key_override: str = None):
        try:
            if idx.empty:
                ident = "ERROR"
                self.identifier = ET.SubElement(self.identifiers,f"{{{self.opexns}}}Identifier") 
                if key_override is None:
                    key_name = "code"
                else:
                    key_name = key_override
                self.identifier.set("type",key_name)
                self.identifier.text = ident
            else:
                for header in self.column_headers:
                    if any(s in header for s in {'Identifier','Archive_Reference','Accession_Reference'}):
                        ident = self.df[header].loc[idx].item()
                        if 'Identifier:' in header:
                            key_name = str(header).rsplit(':')[-1]
                        elif key_override is None:
                            if 'Archive_Reference' in header:
                                key_name = "code"
                            elif 'Accession_Reference' in header:
                                key_name = "accref"
                            elif 'Identifier' in header:
                                key_name = "code"
                        else:
                            key_name = key_override
                    else:
                        ident = None
                    if str(ident).lower() in {"nan", "nat"} or not ident:
                        pass
                    else:
                        self.identifier = ET.SubElement(self.identifiers, f"{{{self.opexns}}}Identifier") 
                        self.identifier.set("type", key_name)
                        self.identifier.text = str(ident)
        except Exception as e:
            print('Error looking up Identifiers')
            print(e)            
    
    def check_opex(self, opex_path: str):
        opex_path = opex_path + ".opex" 
        if os.path.exists(win_256_check(opex_path)):
            return False
        else:
            return True

    def write_opex(self, path: str, opexxml: ET.Element):
        opex_path = str(win_256_check(path)) + ".opex"
        opex = ET.indent(opexxml, "  ")
        opex = ET.tostring(opexxml, pretty_print=True, xml_declaration=True, encoding="UTF-8", standalone=True)
        with open(f'{opex_path}', 'w', encoding="UTF-8") as writer:
            writer.write(opex.decode('UTF-8'))
            print('Saved Opex File to: ' + opex_path)
        return opex_path

    def init_df(self):
        if self.autoclass_flag:
            if self.autoclass_flag in {"catalog", "c", "catalog-generic", "cg"}:
                ac = ClassificationGenerator(self.root, output_path = self.output_path, prefix = self.prefix, start_ref = self.startref, empty_flag = self.empty_flag, accession_flag = False)
            elif self.autoclass_flag in {"accession", "a", "accession-generic", "ag", "both", "b", "both-generic", "bg"}:
                ac = ClassificationGenerator(self.root, output_path = self.output_path, prefix = self.prefix, accprefix = self.acc_prefix, start_ref = self.startref, empty_flag = self.empty_flag, accession_flag="File")
            self.df = ac.init_dataframe()
            if self.autoclass_flag in {"accession", "a", "accesion-generic", "ag"}:
                self.df = self.df.drop('Archive_Reference', axis=1)
            self.column_headers = self.df.columns.values.tolist()
            if self.export_flag:
                output_path = define_output_file(self.output_path, self.root, meta_dir_flag = self.meta_dir_flag, output_format = self.output_format)                
                if self.output_format == "xlsx":
                    export_xl(self.df, output_path)
                elif self.output_format == "csv":
                    export_csv(self.df, output_path)
        elif self.input:
            if self.input.endswith('xlsx'):
                self.df = pd.read_excel(self.input)
            elif self.input.endswith('csv'):
                self.df = pd.read_csv(self.input)
            self.column_headers = self.df.columns.values.tolist()
            self.set_input_flags()
        else:
            self.df = None
            self.column_headers = None
                
    def clear_opex(self):
        walk = list(os.walk(self.root))
        for dir, _, files in walk[::-1]:
            for file in files:
                file_path = win_256_check(os.path.join(dir, file))   
                if str(file_path).endswith('.opex'):
                    os.remove(file_path)
                    print(f'Cleared Opex: {file_path}')
    
    def set_input_flags(self):
        if 'Title' in self.column_headers:
            self.title_flag = True
        if 'Description' in self.column_headers:
            self.description_flag = True
        if 'Security' in self.column_headers:
            self.security_flag = True
        if 'SourceID' in self.column_headers:
            self.sourceid_flag = True
        if 'Ignore' in self.column_headers:
            self.ignore_flag = True
        if 'Hash' in self.column_headers and 'Algorithm' in self.column_headers:
            self.hash_from_spread = True
            print("Hash detected in Spreadsheet; taking hashes from spreadsheet")
            time.sleep(3)

    def print_descriptive_xmls(self):
        for file in os.scandir(self.metadata_dir):
            path = os.path.join(self.metadata_dir, file.name)
            print(path)
            xml_file = ET.parse(path)
            root_element = ET.QName(xml_file.find('.'))
            root_element_ln = root_element.localname
            for elem in xml_file.findall(".//"):
                elem_path = xml_file.getelementpath(elem)
                elem = ET.QName(elem)
                elem_lnpath = elem_path.replace(f"{{{elem.namespace}}}", root_element_ln + ":")
                print(elem_lnpath)

    def init_generate_descriptive_metadata(self):
        self.xml_files = []
        for file in os.scandir(self.metadata_dir):
            if file.name.endswith('xml'):
                """
                Generates info on the elements of the XML Files placed in the Metadata directory.
                Composed as a list of dictionaries.
                """
                path = os.path.join(self.metadata_dir, file)
                xml_file = ET.parse(path)
                root_element = ET.QName(xml_file.find('.'))
                root_element_ln = root_element.localname
                root_element_ns = root_element.namespace
                elements_list = []
                for elem in xml_file.findall('.//'):
                    elem_path = xml_file.getelementpath(elem)
                    elem = ET.QName(elem)
                    elem_ln = elem.localname
                    elem_ns = elem.namespace
                    elem_lnpath = elem_path.replace(f"{{{elem_ns}}}", root_element_ln + ":")
                    elements_list.append({"Name": root_element_ln + ":" + elem_ln, "Namespace": elem_ns, "Path": elem_lnpath})

                """
                Compares the column headers in the Spreadsheet against the headers. Filters out non-matching data.
                """
                list_xml = []
                for elem_dict in elements_list:
                    if elem_dict.get('Name') in self.column_headers or elem_dict.get('Path') in self.column_headers:
                        list_xml.append({"Name": elem_dict.get('Name'), "Namespace": elem_dict.get('Namespace'), "Path": elem_dict.get('Path')})
            if len(list_xml) > 0:
                self.xml_files.append({'data': list_xml, 'localname': root_element_ln, 'xmlfile': path})

    def generate_descriptive_metadata(self, xml_desc: ET.Element, idx: int):
        for xml_file in self.xml_files:
            list_xml = xml_file.get('data')
            localname = xml_file.get('localname')
            """
            Composes the data into an xml file.
            """
            if len(list_xml):
                if not idx.empty:
                    xml_new = ET.parse(xml_file.get('xmlfile'))
                    for elem_dict in list_xml:
                        name = elem_dict.get('Name')
                        path = elem_dict.get('Path')
                        ns = elem_dict.get('Namespace')
                        try:
                            if self.metadata_flag in {'e', 'exact'}:
                                val = self.df.loc[idx, path].values[0]
                            elif self.metadata_flag in {'f', 'flat'}:
                                val = self.df.loc[idx, name].values[0]
                            if pd.isnull(val):
                                continue
                            else:
                                if is_datetime64_any_dtype(str(val)):
                                    val = pd.to_datetime(val)
                                    val = datetime.strftime(val, "%Y-%m-%dT%H-%M-%S.00Z")
                        except KeyError as e:
                            print('Key Error: please ensure column header\'s are an exact match...')
                            print(f'Missing Column: {e}')
                            print('Alternatively use flat mode...')
                            time.sleep(3)
                            raise SystemError()
                        except IndexError as e:
                            print("""Index Error; it is likely you have removed or added a file/folder to the directory \
                                after generating the spreadsheet. An opex will still be generated but with no xml metadata. \
                                To ensure metadata match up please regenerate the spreadsheet...""")
                            print(f'Error: {e}')
                            time.sleep(3)
                            break
                        if str(val).lower() in {"nan", "nat"}:
                            continue
                        if self.metadata_flag in {'e','exact'}:
                            n = path.replace(localname + ":", f"{{{ns}}}")
                            elem = xml_new.find(f'/{n}')
                        elif self.metadata_flag in {'f', 'flat'}:
                            n = name.split(':')[-1]
                            elem = xml_new.find(f'//{{{ns}}}{n}')
                        elem.text = str(val)    
                    xml_desc.append(xml_new.find('.'))
                else:
                    pass
            else:
                pass

    def generate_opex_properties(self, xmlroot: ET.Element, idx: int, 
                                 title: str = None, description: str = None, security: str = None):
        self.properties = ET.SubElement(xmlroot, f"{{{self.opexns}}}Properties")
        self.identifiers = ET.SubElement(self.properties, f"{{{self.opexns}}}Identifiers")
        if title:
            self.titlexml = ET.SubElement(self.properties, f"{{{self.opexns}}}Title")
            self.titlexml.text = str(title)
        if description:
            self.descriptionxml = ET.SubElement(self.properties, f"{{{self.opexns}}}Description")
            self.descriptionxml.text = str(description)      
        if security:
            self.securityxml = ET.SubElement(self.properties, f"{{{self.opexns}}}SecurityDescriptor")
            self.securityxml.text = str(security)
        if self.autoclass_flag in {"generic", "g"}:
            self.properties.remove(self.identifiers)
        elif self.autoclass_flag not in {"generic", "g"} or self.input:
            self.ident_df_lookup(idx)
        if self.identifiers is None:
            self.properties.remove(self.identifiers)
        if self.properties is None:
            xmlroot.remove(self.properties)

    def genererate_opex_fixity(self, file_path: str):
        self.fixity = ET.SubElement(self.fixities, f"{{{self.opexns}}}Fixity")        
        self.hash = HashGenerator(algorithm = self.algorithm).hash_generator(file_path)
        self.fixity.set("type", self.algorithm)
        self.fixity.set("value", self.hash)
        self.OMG.list_fixity.append([self.algorithm, self.hash, file_path])
        self.OMG.list_path.append(file_path)

    def main(self):
        if self.print_xmls_flag:
            self.print_descriptive_xmls()
            input("Press Key to Close")
            raise SystemExit()
        print(f"Start time: {self.start_time}")        
        if self.clear_opex_flag:
            self.clear_opex()
            if self.autoclass_flag or self.algorithm or self.input:
                pass
            else:
                self.print_running_time()
                print('Cleared OPEXES. No additional arguments passed, so ending program.'); time.sleep(3)
                raise SystemExit()
        if self.empty_flag:
            ClassificationGenerator(self.root, self.output_path, meta_dir_flag = self.meta_dir_flag).remove_empty_directories()
        if not self.autoclass_flag in {"g", "generic"}:
            self.init_df()
        self.count = 1
        if not self.metadata_flag in {'none', 'n'}:
            self.init_generate_descriptive_metadata()
        OpexDir(self, self.root).generate_opex_dirs(self.root)
        if self.algorithm:
            output_path = define_output_file(self.output_path, self.root, self.meta_dir_flag, output_suffix = "_Fixities", output_format = "txt")
            export_list_txt(self.list_fixity, output_path)
        self.print_running_time()

class OpexDir(OpexManifestGenerator):
    def __init__(self, OMG: OpexManifestGenerator, folder_path: str, title: str = None, description: str = None, security: str = None):
        self.OMG = OMG
        self.root = self.OMG.root
        self.opexns = self.OMG.opexns
        if folder_path.startswith(u'\\\\?\\'):
            self.folder_path = folder_path.replace(u'\\\\?\\', "")
        else:
            self.folder_path = folder_path
        if self.OMG.input or self.OMG.autoclass_flag in {"c", "catalog", "a", "accession", "b", "both", "cg", "catalog-generic", "ag", "accession-generic", "bg", "both-generic"} \
             or self.OMG.ignore_flag or self.OMG.remove_flag or self.OMG.sourceid_flag \
             or self.OMG.title_flag or self.OMG.description_flag or self.OMG.security_flag:
                self.index = self.OMG.index_df_lookup(self.folder_path)
        elif self.OMG.autoclass_flag is None or self.OMG.autoclass_flag in {"g", "generic"}:
            self.index = None
        if self.OMG.ignore_flag or self.OMG.remove_flag:
            if self.OMG.ignore_flag:
                self.ignore = self.OMG.ignore_df_lookup(self.index)
                if self.ignore:
                    return
            if self.OMG.remove_flag:
                self.removal = self.OMG.remove_df_lookup(self.folder_path, self.index)
                if self.removal:
                    return        
        else:
            self.ignore = False
            self.removal = False

        self.xmlroot = ET.Element(f"{{{self.opexns}}}OPEXMetadata", nsmap={"opex":self.opexns})
        self.transfer = ET.SubElement(self.xmlroot, f"{{{self.opexns}}}Transfer")
        self.manifest = ET.SubElement(self.transfer, f"{{{self.opexns}}}Manifest")
        self.folders = ET.SubElement(self.manifest, f"{{{self.opexns}}}Folders")
        self.files = ET.SubElement(self.manifest, f"{{{self.opexns}}}Files")

        if self.OMG.title_flag or self.OMG.description_flag or self.OMG.security_flag:
            self.title, self.description, self.security = self.OMG.meta_df_lookup(self.index) 
        elif self.OMG.autoclass_flag in {"generic", "g", "catalog-generic", "cg", "accession-generic", "ag", "both-generic", "bg"}:
            self.title = os.path.basename(self.folder_path)
            self.description = os.path.basename(self.folder_path)
            self.security = "open"
        else:
            self.title = title
            self.description = description
            self.security = security
        if self.OMG.sourceid_flag:
            self.OMG.sourceid_df_lookup(self.transfer, self.folder_path, self.index)
        if self.OMG.autoclass_flag or self.OMG.input:
            self.OMG.generate_opex_properties(self.xmlroot, self.index, 
                                              title = self.title,
                                              description = self.description,
                                              security = self.security)
            if not self.OMG.metadata_flag in {'none', 'n'}:
                self.xml_descmeta = ET.SubElement(self.xmlroot,f"{{{self.opexns}}}DescriptiveMetadata")
                self.OMG.generate_descriptive_metadata(self.xmlroot, idx = self.index)

    def filter_directories(self, directory: str):
        if self.OMG.hidden_flag is False:
            list_directories = sorted([os.path.join(directory, f.name) for f in os.scandir(directory)
                                       if not f.name.startswith('.')
                                       and not bool(os.stat(os.path.join(directory, f.name)).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)
                                       and f.name != 'meta'
                                       and f.name != os.path.basename(__file__)]
                                       , key=str.casefold)
        elif self.OMG.hidden_flag is True:
            list_directories = sorted([os.path.join(directory, f.name) for f in os.scandir(directory) \
                                       if f.name != 'meta' \
                                       and f.name != os.path.basename(__file__)], key=str.casefold)
        return list_directories
        
    def generate_opex_dirs(self, path: str):
        self = OpexDir(self.OMG, path)
        opex_path = os.path.join(os.path.abspath(self.folder_path), os.path.basename(self.folder_path))
        for f_path in self.filter_directories(path):
            if f_path.endswith('.opex'):
                pass
            elif os.path.isdir(f_path):
                if not self.ignore:
                    self.folder = ET.SubElement(self.folders, f"{{{self.opexns}}}Folder")
                    self.folder.text = str(os.path.basename(f_path))
                self.generate_opex_dirs(f_path)
            else:
                OpexFile(self.OMG, f_path, self.OMG.algorithm)
        if self.OMG.check_opex(opex_path):
            if not self.ignore:
                for f_path in self.filter_directories(path):
                    if os.path.isfile(f_path):
                        file = ET.SubElement(self.files, f"{{{self.opexns}}}File")
                        if f_path.endswith('.opex'):
                            file.set("type", "metadata")
                        else:
                            file.set("type", "content")
                            file.set("size", str(os.path.getsize(f_path)))
                        file.text = str(os.path.basename(f_path))
                self.OMG.write_opex(opex_path, self.xmlroot)
        else:
            print(f"Avoiding override, Opex exists at: {opex_path}")

class OpexFile(OpexManifestGenerator):
    def __init__(self, OMG: OpexManifestGenerator, file_path: str, algorithm: str = None, title: str = None, description: str = None, security: str = None):
        self.OMG = OMG
        self.opexns = self.OMG.opexns  
        if file_path.startswith(u'\\\\?\\'):
            self.file_path = file_path.replace(u'\\\\?\\', "")
        else:
            self.file_path = file_path
        if self.OMG.check_opex(self.file_path):
            if self.OMG.input or self.OMG.autoclass_flag in {"c","catalog","a","accession","b","both","cg","catalog-generic","ag","accession-generic","bg","both-generic"} \
                or self.OMG.ignore_flag or self.OMG.remove_flag or self.OMG.sourceid_flag \
                or self.OMG.title_flag or self.OMG.description_flag or self.OMG.security_flag:
                    self.index = self.OMG.index_df_lookup(self.file_path)
            elif self.OMG.autoclass_flag is None or self.OMG.autoclass_flag in {"g","generic"}:
                self.index = None
            if self.OMG.ignore_flag:
                self.ignore = self.OMG.ignore_df_lookup(self.file_path, self.index)
                if self.ignore:
                    return
            if self.OMG.remove_flag:
                removal = self.OMG.remove_df_lookup(self.file_path, self.index)
                if removal:
                    return                
            else:
                self.ignore = False
            self.algorithm = algorithm
            if self.OMG.title_flag or self.OMG.description_flag or self.OMG.security_flag:
                self.title, self.description, self.security = self.OMG.meta_df_lookup(self.index) 
            elif self.OMG.autoclass_flag in {"generic", "g", "catalog-generic", "cg", "accession-generic", "ag", "both-generic", "bg"}:
                self.title = os.path.splitext(os.path.basename(self.file_path))[0]
                self.description = os.path.splitext(os.path.basename(self.file_path))[0]
                self.security = "open"
            else:
                self.title = title
                self.description = description
                self.security = security
            if self.OMG.algorithm or self.OMG.autoclass_flag or self.OMG.input:
                self.xmlroot = ET.Element(f"{{{self.opexns}}}OPEXMetadata", nsmap={"opex":self.opexns})
                self.transfer = ET.SubElement(self.xmlroot, f"{{{self.opexns}}}Transfer")
                if self.OMG.sourceid_flag:
                    self.OMG.sourceid_df_lookup(self.transfer, self.file_path)
                if self.OMG.algorithm:
                    self.fixities = ET.SubElement(self.transfer, f"{{{self.opexns}}}Fixities")
                    if self.OMG.hash_from_spread:
                        self.OMG.hash_df_lookup(self.file_path, self.fixities, self.index)  
                    else:
                        self.genererate_opex_fixity(self.file_path)
                if self.transfer is None:
                    self.xmlroot.remove(self.transfer)
                if self.OMG.autoclass_flag or self.OMG.input:
                    self.OMG.generate_opex_properties(self.xmlroot, self.index,
                                                      title = self.title,
                                                      description = self.description,
                                                      security = self.security)
                    if not self.OMG.metadata_flag in {'none','n'}:
                        self.xml_descmeta = ET.SubElement(self.xmlroot, f"{{{self.opexns}}}DescriptiveMetadata")
                        self.OMG.generate_descriptive_metadata(self.xml_descmeta, self.index)
                opex_path = self.OMG.write_opex(self.file_path, self.xmlroot)
                if self.OMG.zip_flag:
                    zip_opex(self.file_path, opex_path)
        else:
            print(f"Avoiding override, Opex exists at: {self.file_path}: ")