# FluentCleaner distribution

This directory contains the unmodified Modern x64 release from builtbybel/FluentCleaner,
version 26.09.01. Classic was not integrated because its edition-specific UI source is
not public. The integration launches the Modern UI as a separate process without
`/AUTO` or `/SHUTDOWN`.

- Upstream: https://github.com/builtbybel/FluentCleaner
- Release: https://github.com/builtbybel/FluentCleaner/releases/tag/26.09.01
- Source tag commit: 2e3408e5e519f4ec5db4e095dbf28908d5728a52
- Archive: FluentCleaner-win-x64.zip
- Archive SHA-256: 570d73ee702e888ecc3db2af583dd24428cd6f59a26edf1a1c0dbdc2552613b3

The release archive was verified against the digest returned by GitHub's release API.
Debug PDB files were omitted. All other extracted release files are enumerated in
release-manifest.json; that manifest is checked before copying and launching the app.
Licenses and this integration note were added alongside the original files.
This is an integrity check, not a claim of an antivirus verdict or reproducible build.

FluentCleaner is MIT licensed; see LICENSE. The unchanged Winapp2.ini database is
copyright its Winapp2 contributors and distributed under CC BY-SA 4.0. Its original
attribution is retained in the file header. See WINAPP2-LICENSE.md and
https://github.com/MoscaDotTo/Winapp2. These database terms apply to the database,
not as a replacement license for the host application. The bundled .NET runtime
notices are in DOTNET-LICENSE.TXT and DOTNET-THIRD-PARTY-NOTICES.TXT.

The first launch copies this pinned distribution to:
`%LOCALAPPDATA%\ITToolSAGSCXR\tools\FluentCleaner\26.09.01`.
This allows the cleaner to remain running after IT Tool closes. If a pinned file is
changed or an unexpected EXE/DLL appears, launch is refused with a visible error.
Upstream database/customization changes may therefore require restoring the pinned
distribution. The integration does not silently replace modified user data or
automatically install updates/runtime components.

Modern requires Windows x64 and Windows App Runtime 2.0.1 x64 as documented by
upstream. The UI includes the official Microsoft download link when needed.

From IT Tool 1.0.1, launch preserves the user's existing settings and adds global
PATH exclusions for the ITToolSAGSCXR directory and the host's live extraction
directory. This prevents cleanup from deleting the application's own dependencies.
