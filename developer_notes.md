## Documentation
https://secure.na1.adobesign.com/public/docs/restapi/v6
https://github.com/adobe-sign/rest-api-sample
https://github.com/adobe-sign/AdobeSign-OpenAPI

## Agreement Endpoints
1. Get /agreements
```json
{
    "userAgreementList": [
        {
            "displayDate": "2026-03-23T19:06:40Z",
            "name": "ACLARACIONES ESPECIALES 23-03-2026",
            "id": "CBJCHBCAABAAhKUCj1JU1fOIRHMnMdz6sOudjQX4rXhM",
            "status": "SIGNED",
            "type": "AGREEMENT",

            "displayParticipantSetInfos": [
                    {
                        "displayUserSetMemberInfos": [
                            {
                                "email": "rose.gutierrez@bci.cl",
                                "company": "BANCO DE CREDITO E INVERSIONES - BCI",
                                "fullName": "Rose Marie Gutierrez Perez",
                                "deliverableEmail": true
                            }
                        ]
                    }
                ],
        },
    ],
    "page": {
        "nextCursor": "MTc2MjI4MjE4NzAwMCxDQkpDSEJDQUFCQUFMWm9nMGhuYXNZTlRQTjJ3N0lWdGtaWC1MNU5TbnJucw%3D%3D"
     }
}```

2. Search
```json
{
    "totalHits":
}
```


## DB TABLES
# SQLite
# User DB
    id INTEGER PRIMARY KEY,
    email varchar (250) NOT NULL UNIQUE, // FK
    user_id varchar (250) NOT NULL UNIQUE, // FK
    company varchar (250)

# Group DB
    id INTEGER PRIMARY KEY,
    groupid varchar (250) NOT NULL UNIQUE,
    groupname varchar (250)

# Agreement DB   

## SQL Alchemy