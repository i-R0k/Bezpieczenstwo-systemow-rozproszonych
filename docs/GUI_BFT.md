# GUI BFT dashboard

Harmonogram projektu obejmowal GUI do wizualizacji topologii, rund konsensusu, zdarzen systemowych, membership i recovery.

Repo zawiera prosty dashboard HTML bez React/Vue:

- `GET /bft/dashboard` - statyczna strona `VetClinic/API/vetclinic_api/static/bft_dashboard.html`;
- `GET /bft/communication/log` - logiczny dziennik komunikacji oparty o `EventLog`.

## Zakres wizualizacji

Dashboard pokazuje:

- cluster nodes i quorum;
- SWIM membership;
- HotStuff current view, leader i commits;
- Narwhal DAG summary;
- fault injection summary;
- checkpoint/recovery summary;
- crypto/security summary;
- recent events;
- communication log.

## Technika

Strona uzywa `fetch` i okresowego polling. Nie ma WebSocket ani osobnego frontendu. Wszystkie dane pochodza z istniejacych endpointow `/bft/*`.

Communication log jest logicznym widokiem zdarzen protokolow, a nie packet capture. `source_node_id`, `target_node_id`, `message_kind` i `signed_message_id` sa pobierane z `details`, gdy dany event je zawiera. Starsze eventy bez tych pol zwracaja `null`.

## Ograniczenia

- Dashboard jest demonstracyjny.
- Nie wykonuje destrukcyjnych POST/PUT/DELETE.
- Nie pokazuje realnych pakietow sieciowych.
- Brak WebSocket i push updates.
