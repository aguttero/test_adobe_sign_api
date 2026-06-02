# Worflow 6 TEST
## test ok
1. 759 - CBJCHBCAABAA-t9NJfmwxJgPZby4BpezQ256Q9koTDUY
2. 766 - CBJCHBCAABAA_AL2p5mrLyksv7oY8HhlyMPb5AbhSGIq
3. 767 - CBJCHBCAABAABs5JwBWb2JaSHApcbwicD-THKQ7oOL_m
4. 801 - CBJCHBCAABAApLxW-kW-a_LC9UClFxVcRt4ZpbPVoKbT
5. 871 - CBJCHBCAABAAke5ku2eEH_jR2UAjuKcuVT8az2uMe6EI
6. 885 - EDGE CASE - No encuentra RUT
7. 889 - EDGE CASE - gerenncia_solicitante= None
8. 1195 - CBJCHBCAABAAcAOdafnz8yPeKgzhedX3UXBrm16_HqI4
9. 1570 - EDGE CASE - toma el 2025 como Cuenta Contable CBJCHBCAABAAYARob0IVL0UhIPKxTshuZW-IkfAVKWyZ
10. 2368 - CBJCHBCAABAAsCMMrkMsddLn_pdWXoAjIxk4_SVXZ0fs
11. 3165 - CBJCHBCAABAAkjBy--jGnJzRpIebK5qHx4r8JT1JIzQF


## edge cases
6. 885 - CBJCHBCAABAALuqZmF8io5IxI_J7RaZ6jOa027m_vVkP - No encuentra RUT - 3 x Centro de Costos, Cuenta Contable, Orden controlling
7. 889 - CBJCHBCAABAAU7IoQdZRsYlcYMIiP24XOsnEu8R48Ycl - Sin Gerencia solicitante.


2026-06-02 15:22:26,285 [DEBUG] database.insert_jad_content — Found agreement pkid= 885 for agreement_id= CBJCHBCAABAALuqZmF8io5IxI_J7RaZ6jOa027m_vVkP
Traceback (most recent call last):
  File "/Users/aleguttero/code_loc/test_adobe_sign_api/src/main.py", line 752, in <module>
    exit_code: int = dev_main()
                     ~~~~~~~~^^
  File "/Users/aleguttero/code_loc/test_adobe_sign_api/src/main.py", line 675, in dev_main
    parse_result = parse_documents(agreements_found)
  File "/Users/aleguttero/code_loc/test_adobe_sign_api/src/main.py", line 459, in parse_documents
    result = db.insert_jad_content(agreement_id, result_dict)
  File "/Users/aleguttero/code_loc/test_adobe_sign_api/src/database.py", line 866, in insert_jad_content
    rut_proveedor=input_dict["rut_proveedor"],
                  ~~~~~~~~~~^^^^^^^^^^^^^^^^^
KeyError: 'rut_proveedor'
(.venv) aleguttero@MacBook-Pro test_adobe_sign_api %
