# Parish fields

The parish CSV carries a location and an image for each parish. Partner exports often leave them empty; the conventions below govern how they are filled afterwards, by hand or by script, from Wikipedia, Wikidata and GeoNames.

## Location

`location` is PostGIS EWKT, `SRID=4326;POINT (lon lat)`, longitude first. The tool reads it from `B_Umfang` as `lat, lon` and swaps the order.

The column is a findability aid that helps people locate a parish, not an official location, so an approximate point beats a blank.

### Which point

- A parish spanning several villages (`Azmoos-Trübbach`, `Thal & Rheineck`, `Sennwald-…`) gets the first-named place. That is the principal parish seat, where the church almost always stands; the centroid of the components can land in a field.
- A St. Gallen city parish named after a church gets that church's own coordinates.
- Related parishes may share a point, since they share a seat: four Sennwald rows, two Azmoos, two Thal.
- A link that resolves to a containing municipality (`Niederuzwil` → `Uzwil`, `Vilters`/`Wangs` → `Vilters-Wangs`, `Walde` → `Eschenbach SG`) is never filled from that municipality. Its centroid is a plausible but wrong point, and two parishes resolving to one merged municipality get identical coordinates.

### Sources for St. Gallen

GeoNames is the primary source. The `CH.zip` dump from <https://download.geonames.org/export/dump/> needs no API key. Filtering country `CH`, admin1 `SG` and feature class `P` makes wrong-canton matches impossible and yields about 580 places. GeoNames has village-level entries where de.wikipedia only redirects to the containing municipality (Niederuzwil, Vilters, Wangs, Walde), so it fills rows Wikipedia cannot. GeoNames is CC BY 4.0: published output needs attribution.

The de.wikipedia article in `parish_church_link` is the second source. Verify every candidate against Wikidata P131 up to Kanton St. Gallen, Q12746 (Q11911 is Kanton Bern). Where P131 is absent, as for `Murg SG` (Q99437597), fall back to a canton bounding box. Bare place-name links are the main hazard: they can be disambiguation pages or a real article in the wrong country (`Waldkirch` → the town in Baden-Württemberg, not `Waldkirch SG`), which a coordinates-only lookup accepts silently.

Use each source as a check on the other. Agreement within about 3 km is good evidence; disagreement flags an error in one of them.

English Wikipedia is not used. It covered 20 of 35 test names, rounds coordinates to arcminutes, has no articles for the St. Gallen city parishes and lacks canton disambiguation (`Krummenau` → the village in Rhineland-Palatinate, `Kappel, Switzerland` → Kanton Solothurn). Every village it does resolve redirects to the containing municipality.

## Image

`image_url` is the direct `https://upload.wikimedia.org/...` file URL. `image_source` is the credit line `Foto: Wikipedia <Author> / <License>`, for example `Foto: Wikipedia Franc rc / Creative Commons CC0 License`. The license renders as `Creative Commons <LicenseShortName> License` for any Creative Commons license and as the plain name otherwise (`Public Domain`, `Free Art License`). The tool reads them from `B_Nachfolger` and `B_Provenienz`.

`image_path` stays empty: Matricula fills it with its own mirrored copy on import.

### Filling from Wikipedia

Take the lead image via `prop=pageimages` on the article in `parish_church_link`. Then query `prop=imageinfo&iiprop=extmetadata` on Commons, falling back to de.wikipedia for local uploads, for `Artist` and `LicenseShortName`. Strip the HTML anchor markup from `Artist` and drop a leading `User:`.

For a parish whose link has no article, use the place that supplied the coordinate, so picture and pin agree.

### Traps in the Wikimedia APIs

- `pageimages` returns filenames with underscores, while `imageinfo` titles come back with spaces. Key both the same way, or almost every lookup misses.
- Wikimedia appends `?utm_source=…` tracking parameters to both `pageimages.original.source` and `imageinfo.url`. Strip the query string.
- The lead image is often a municipality map or coat of arms, not a photo (`Karte_Gemeinde_*`, `*-blazon.svg`, `Gemeinde_*_einfach.png`). Crediting those as "Foto:" is false. Detect them and take the first real photograph from `action=parse&prop=images`, which lists images in page order, or leave the row empty.

Bulk HEAD requests to `upload.wikimedia.org` are rate-limited with 429 quickly. The API-supplied URLs are canonical by construction, so spot-check a few slowly instead of verifying all of them.
