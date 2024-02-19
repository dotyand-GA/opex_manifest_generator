# Opex Manifest Generator Tool

The Opex Manifest Generator is a pythom programme for generating OPEX files for use with Preservica and system's compatable with the OPEX standard. It will recursively go through a 'root' directory and generate an OPEX files for each folder or, depending on specified options, files.

## Why use this tool?

This tool was primarily intended to allow users of local systems, to undertake larger uploads safetly utilising the mass ingest, utilising the Opex Ingest Workflow - with Manifest's checked. However, it has been tested as functioning with:
- PUT Tool
- Manual Ingest
- Uploading via UX2

In theory, it should be compatiable with any system that makes use of the OPEX standard. But in theory Communism works, in theory.

## Additional features:

There are a number of additional feature's utilised including:
- Generating Fixities for Files, with SHA1, MD5, SHA256, SHA512 (Default is SHA1)
- OPEX's can also be cleared, for repeated / ease of use.

Making use of The Auto Classification Generator, a host of other feature's are available.
- Reference's can be automatically generated and assigned by a simple command.
- The Archive / Accession mode's
- Clear and log Empty folders.
- All the feature's available through the Auto Classification Tool are avialable here.

A major feature of this is that the spreadsheet can also act as an input, meaning you can generate an "AutoClass" spreadsheet, utilise this to assign metadata on import. Currently this allows:
- Assignment of Title, Description, and Security Status fields on upload.  
- Assignment of standard and custom xml metadata templates on upload. *requires a small bit of setup*

## Prerequisites

The following modules are utilised and installed with the package:
- auto_classification_generator
- pandas
- openpyxl
- lxml

Python Version 3.8+ is also recommended. It may work on earlier versions, but this has not been tested. 

It is OS independent and should work on Windows, MacOS and Linux.

## Installation

To install, simply run:

`pip install -U opex_manifest_generator`

## Usage

### Folder Manifest Generation
To run the basic program, run from the terminal:

`opex_generate {path/to/your/folder}`

For instance, on Windows:

`opex_generate "C:\Users\Christopher\Downloads\"`

Running this command without additional options will restrict the generation to only folder manifests. This will act recursively, so every folder within that folder, will have an Opex Generated. This is geared toward's simple usage, with the Opex Ingest Workflow.

### Fixity Generation

To expand the capabilites, I can add the fixity option like so:

`opex_generate "C:\Users\Christopher\Downloads\" -fx`

This will run and generate Fixities for each individual files. To note when generating, the folder OPEX's also inculdes, the newly generated Opex files as part of it's manifest as required.

To utilise a different algorithm:

`opex_generate "C:\Users\Christopher\Downloads\" -fx -alg SHA-256`

This is intended to add an additional check in our Opex Ingest workflow, ensuring that the content is safely delivered with matching Hashes.

### Zipping 

I could also utilise the zip option to bundle the opex and content into a zip file.

`opex_generate "C:\Users\Christopher\Downloads\" -fx -alg SHA-1 -z`

This allows for use with manual ingest or into the new UX2. Currently, no files will be removed after the zipping, so bare in mind the space you have available.

Also be aware that running this command multiple times will break existing opex files.

### Clearing Opex's

If you're experimenting or simply make a mistake, the clear option will remove all existing Opex's in a directory.

`opex_generate "C:\Users\Christopher\Downloads\" -clr`

Running this command with no additional option will end after clearing the Opex's if other options are enabled it will proceed with the generation.

## Use with the Auto Classification Generator

My other tool, the Auto Classification Generator, is built into this tool. While use of these features is options, if only the above scenario's are needed; making use of this allows for custom assignment of XIP data and identifiers.

The tool will, instead of exporting to a spreadsheet, directly embed the references into the Opex file.

To avoid potential conflicts / unwanted data getting into Preservica, the behaviour differs when compared to utilising the standalone command. Auto Class options can be freely combined with the Opex options. When utilising `--auto_class` files will always be given an Opex.

## Basic Generation.

To generate an auto classification code simply run:

`opex_generate -c catalog -p "ARCH" C:\Users\Christopher\Downloads`

This will generate Opex's with an identifier "code" added to each of the files. As described in the Auto Class module, the reference codes will take the hierachy of the directories.

### Use of Auto Classification as an Input 

This program also support utilising existing Auto Classification spreadsheets as an input, instead of generating them on command.

In this way, you can utilise these to set: Title, Description and Security Status data on ingest. Xml metadata templates can also be set on ingest.

#### XIP metadata

To create a spreadsheet of my directory: `C:\Users\Christopher\Downloads` with references ARCH, with run:

`opex_generate -c catalog -p "ARCH" -ex "C:\Users\Christopher\Downloads"` or `auto_class -p "ARCH" "C:\Users\Christopher\Downloads"` to avoid unnecessary OPEX creation.

In the resultant spreadsheet, you would then add in "Title", "Description", and "Security" as new columns. Then populate these with information.

Simply run to intialise the generation: `opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}"`

Please note, if your root directory isn't a match or if there are any changes to the hierachy data after export of the intial spreadsheet, may not be assigned correctly.

#### XML Metadata

To utilise an import with XML Metadata templates, first the XML template has to be stord the source 'metadata' directory. DC, MODS, GPDR, and EAD templates come with the package, but custom templates can be added and will work 'out-the-box', as long as they are functioning within Preservica. *I will likely change the destination of this directory for easier use.

After exporting an Auto Class spreadsheet, you then need to add in additional columns for the field.All fields are optional, and can added on a drop-in basis. The title of column is case sensistive to the tag, and has to include the namespace.

Fields can added in two ways: 'exactly' or 'flatly'.

Explicitly requires that the full path from the XML document is added to the column, with parents / child seperated by a `/`; while 'flatly' requires only a matching end tag. For example, the below will match to the same recordIdentifer field in mods:

```
Exactly:
mods:recordInfo/mods:recordIdentifier

Flatly:
mods:recordIdentifier
```

While using the flat method is easier, if there's non-unique tags - such as "note" in MODS - the flat method will only import to the first match, which might not be it's intended destination. 
Also when 'exactly' importing multiple's of the same tag, at the same level - again such as "note" in MODS - you will need add an index in square brackets such as: `mods:note[1] mods:notes[2] ...` The number to add will be the order they appear in the XML.

This is all probably easier done, than said :\). For convience I've also included uploaded spreadsheet templates of DC, MODS, GDPR and EAD, with thier explict names.

Once you've got the above setup to create the Opex's simply run, depending on your choice of:
`opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}" -m flat` or 
`opex_generate -i "{/path/to/your/spreadsheet.xlsx}" "{/path/to/root/directory}" -m exact`

## Options:

The following options are currently avilable to run the program with, and can be utilised in various combinations with each other, although some combinations will clash:

```
Options:
        -h,     --help          Show Help dialog

    Opex Options:

        -fx,  --fixity      Generate a Fixity Check for files.                      [boolean]
        
        -alg  --algorithm   Set to specify which algorithm to use                   {SHA-1,MD5,SHA-256,SHA-512} 
                            for fixity. Defaults to SHA-1.
        
        -rm,  --empty       Remove and log empty directories in a structure         [boolean]
                            Log will bee exported to 'meta' / output folder

        -clr, --clear-opex  Will remove all existing Opex folders,                  [boolean]
                            When utilised with no other options, will end
                            the program.
        
        -z,   --zip         Will zip the Opex's with the file itself to create      [boolean]
                            a zip file. Existing file's are currently not removed.
                            ***Use with caution, repeating the command multiple 
                            times, will break the Opex's.

    Auto Classification Options:

        -c,  --autoclass    This will utilise the AutoClassification                {catalog, accession, both, generic,
                            module to generate an Auto Class spreadsheet.            catalog-generic, accesison-generic,
                                                                                     both-generic}
                            There are several options, {catalog} will generate
                            a Archival Reference following; {accession}
                            will create a running number of files
                            (Currently this is not configurable).
                            {both} will do Both!
                            {generic} will populate the Title and 
                            Description fields with the folder/file's name,
                            if used in conjunction with one of the above options:
                            {generic-catalog,generic-accession, generic-both}
                            it will do both simutaneously.
                            For more details on these see the 
                            auto_classification_generator page.
        
        -p,   --prefix      Assign a prefix to the Auto Classification,             [string]
                            when utilising {both} fill in like:
                            "catalog-prefix","accession-prefix".            
        
        -o,   --output      Set's the output of the 'meta' folder when              [string] 
                            utilising AutoClass.
                                
        -s,   --start-ref   Sets the starting Reference in the Auto Class           [int]
                            process.

        -i    --input       Set whether to use an Auto Class spreadsheet as an      [string]
                            input. The input needs to be the (relative or
                            absolute) path of the spreadsheet.

                            This allows for use of the Auto Class spreadsheet
                            to customise the XIP metadata (and custom xml 
                            metadata).

                            The following fields have to be added to the
                            spreadsheet and titled exactly as:
                            Title, Description, Security.

        -m    --metadata    Toggles use of the metadata import method.              {none,flat,exact}
                            There are two methods utilised by this:
                            {none,exact,flat}. None ignores metadata import
                                
                            Exact requires that the column names in the spread
                            sheet match exactly to the XML:
                            {example:path/example:to/example:thing}
                            Flat only requires the final tag match.
                            IE {example:thing}. However, for more complex sets
                            of metadata, Flat will not function corrrectly. 
                            Enabled -m without specification will use exact,
                            method.
                                
                            Use of metadata requires, an XML document to 
                            be added to the metadata folder, see docs for
                            details (currently in site-packages *may change).

        -dmd, --disable-    Will, disable the creation of the meta.                 [boolean]
                meta-dir    Can also be enabled with output.
  
        -ex     --export    Set whether to export the Auto Class, default
                            behaviour will not create a new spreadsheet.

        -fmt,   --format    Set whether to export as a CSV or XLSX file.           {csv,xlsx}
                            Otherwise defualts to xlsx.
```

## Future Developments

- Adjust Accession so the different modes can utilised from Opex.
- Add SourceID as option for use with Auto Class Spreadsheets.
- Allow for multiple Identifier's to be added with Auto Class Spreadsheets. Currently only 1 or 2 identifers can be added at a time, under "Archive_Reference" or "Accesion_Refernce". These are also tied to be either "code" or "accref". An Option needs to be added to allow cutom setting of identifier...
- Develop Zipping to conform to PAX.
- Add an option / default for Metadata XML's to be located in a specified directory rather than in src.

## Contributing

I welcome further contributions and feedback.