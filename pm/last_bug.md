

### bugs
756 - 4 - CBJCHBCAABAAEo3ssinHykRIq-BJu_qP6gLxS9G-L63E- DB error
approver with double role


### prompt
i am building a database to track an agreement workflow, with approvers and signers. I have an 'agreements' table and a 'signers_approvers' Table. Each agreement can have multiple signers/approvers. Each signer/approver has a role (service owner, buyer, manager1, manager2, manager3). The same email can be listed more than once for each agreement, as this email might have more than one role in the same agreement. (for example: service owner and manager 1). The 'signers_approvers' table has these fields: pk_id, agreement_id, signer_email, signer_role, signer_order. The PK is pk_id field (int). I am working in python + SQLA + SQLite. I receive the signers/approvers email list for each agreement_id in a json from one api call that brings all agreements and all signers. I  insert the signers/approvers in the 'signers_approvers' table for each agreement_id. Then for each agreement_id i receive the signer_email, signer_role and signer_order from a different api call. I now need to update the 'signers_approvers' table but have issues while trying to update the table when the same email appears twice in this table for the given agreement. How should i code the update statement? 
  
# PENDING
* mecanismo de validacion para casos manuales (3 x cta contable)
* find out sleep time needed to throtle the download api call queue
* define document status and timestamp for manual, qa, reviewed and reported
* add IA image flow processing

(.venv) aleguttero@MacBook-Pro test_adobe_sign_api %
