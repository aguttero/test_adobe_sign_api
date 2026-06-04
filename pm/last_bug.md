# Workflow 5 TEST
## Donwload
* revisar log /Users/aleguttero/code_loc/test_adobe_sign_api/logs/20260603_07_56.log
* descarga 31 files de 74 (determinar error)
* agregar una pausa en el for loop para no 
* hacer parse

## Lista de 74 agreement_id:
2026-06-03 07:56:25,961 [DEBUG] database.fetch_agrmnt_by_wkflow — result_type= <class 'list'> - result= ['CBJCHBCAABAAXg03Zv0sOUIT9uRpC8TxetCLy2mbX3py', 'CBJCHBCAABAAvHdMlVnDWgsJ3cQTg0_R0WU7LRlRvq8k', 'CBJCHBCAABAAriDB0If6cc0WWXo9hj_XqID4S6mT2S8_', 'CBJCHBCAABAAEo3ssinHykRIq-BJu_qP6gLxS9G-L63E', 'CBJCHBCAABAAOvLLcrivWnHW2-_ZJRkWk4HlalAkHvp7', 'CBJCHBCAABAAvHZXdcgy6WWrak1s-yhuGkRcTVF_KTaC', 'CBJCHBCAABAA3Z_hXO-FsiTzlHULCTuq9n5jsxFXjxtZ', 'CBJCHBCAABAAX7v7DlHrx-YpuwrzLLL7-ZVeECV9sR9r', 'CBJCHBCAABAA8qNcGihIEsNtVsF0IPVswyl5PdZfTK-1', 'CBJCHBCAABAA7_KjDGA9QvfUrpCgU8EXxTrGvc2uqhrn', 'CBJCHBCAABAAwCzrLSboqGy6c-nLs5OiUEDz5EwpDlrf', 'CBJCHBCAABAAH0Gl_Cf3ELEIhMdaOaY1iWGm7TPF0jnm', 'CBJCHBCAABAAYbYw5V9BhiUqfvZam6-GCJGVnGihGOi4', 'CBJCHBCAABAAg4IUbE0EfzxGg6VMi48LfTIIXpVsacGi', 'CBJCHBCAABAAChccctCDP5ETO0a1Cp6LKA6x1KLnKGGS', 'CBJCHBCAABAAg4qcjSwk5rLcVM4c3R-Imdz4lW6PpSU0', 'CBJCHBCAABAAK5CXJ240FQEi6MvvGfZqhtW_4Mgmmgba', 'CBJCHBCAABAAX29zlYLMX5ZoCnybv8-dPDxtrsg6zKEi', 'CBJCHBCAABAA2794TgGmVxvWBu-5rqYz57cB33DM1QnU', 'CBJCHBCAABAAw_TJhYlobFb_Y2kKasEmm7boQ94B4Oig', 'CBJCHBCAABAAqpzkza_nq6m2bIxzTDq-eqEKuGzuwf0i', 'CBJCHBCAABAAUI1LjFGCLnuFhf6SLIWjVtr7YosfRJvv', 'CBJCHBCAABAA0XyVJ-j4xeYjmlJBOxRNf6lYrUkW7qGo', 'CBJCHBCAABAAyRJG6yN-Yfblv2_omgARb-ZZak1fYqgi', 'CBJCHBCAABAAzvkr9Tkbuf07n2v_08_gypmWvYPaLJan', 'CBJCHBCAABAAArJTZxkqWbEn4R8N1Zq6w9nGY_7ukQIL', 'CBJCHBCAABAAjYT5-lCBnDMEvhlCBAUFLq6XAJsgzWyt', 'CBJCHBCAABAA4iW-nBSTCOwY67Hd7MpjBLbUQ0fPjdQ_', 'CBJCHBCAABAATaKaSvkS8ePQdbbeT64zrE7p7EjtxFjU', 'CBJCHBCAABAAM4Kr6qmyNAX9FzRmziXHcDG3XdqiBWH0', 'CBJCHBCAABAAd4JE_zufZrjE4En42MjJidddJxb5HGmo', 'CBJCHBCAABAAV-SrVa4iwRO2hYgZo04ny14C0TINAo6B', 'CBJCHBCAABAAFUHMd-6bJwvNIOp2-EHePJvCJUk7khUL', 'CBJCHBCAABAAQ8xJ6C6JPQJ6ESXNsIzSXiB-a0CyvL71', 'CBJCHBCAABAAE7GUn4K2Und5OrezsdX5M2rKX-ROvKRC', 'CBJCHBCAABAABtu2VKqs9IBtgbHDOPQpTywCaSeLYQU6', 'CBJCHBCAABAAePATM7-4hz5G0-_VWu78bE3AyW0ko2jM', 'CBJCHBCAABAAYTf5QcEs-0Jey_6hw60JJwj7vav4PLKV', 'CBJCHBCAABAAMqBxmBvo-KS-o8jp3kRILAjFahOVMKtm', 'CBJCHBCAABAAXLj2skLka5tYWZeWhE-XXEPQo8FF2ZW7', 'CBJCHBCAABAAEzIHcAB0DenLdfHy_UAS38AYNDt20bnN', 'CBJCHBCAABAAjW9THcTLye_LUIzar7CssGH0BaDs679H', 'CBJCHBCAABAAhCCYOqKsnOsqYWo00YYzJU1mF8Mdl0f3', 'CBJCHBCAABAAtG5H6nDRK0Q3MFfobu7JvDNp3LLWz44-', 'CBJCHBCAABAAyHkHHlAV5_nIOM2O2EI_GzBK-kAWmc_m', 'CBJCHBCAABAABKWXO3khf6iPoeTMvz8VxXmnzHm7iGtx', 'CBJCHBCAABAAUTV5atx4LzlzMhxwrz1NNm9DtAHPzPMB', 'CBJCHBCAABAAptSCU8hxQBKW6EcbTkV8LPWdQ1gR2peZ', 'CBJCHBCAABAARofvbODu5-ctzAgwNmlpDEperoKiXUy1', 'CBJCHBCAABAAT1BBuf8MIuVVQdkJFZ5kHXJ9nT2eEcXf', 'CBJCHBCAABAAyow6UE7hKzU1_6ovwd1TsA-2I3GwXMDB', 'CBJCHBCAABAAsN0AioKD7v1yuSkvtPVR_EegFaSrRa8T', 'CBJCHBCAABAACDBriOhyDXPe_kvgx0A9CQzEq2NSJvD2', 'CBJCHBCAABAAPe1F8bPJbPfYPsJcY_lf5sBytQqWuFob', 'CBJCHBCAABAAl2FjsMonk76hsBjliJ6AoRh5M1AtCxax', 'CBJCHBCAABAAkt9xMvHudtIOQZx8p9Wn3nA4sU3ZU9Z1', 'CBJCHBCAABAAOo0URV6G9eDJg7AqURIvikC0WNR85R-0', 'CBJCHBCAABAAWIbMDOEgcYkTmXL-XT5escB-e5CcsPyO', 'CBJCHBCAABAANQMghsSh0P0d1tH1Mow8O_XJGFPxkZub', 'CBJCHBCAABAA6-EuOPVdTTYqiDVcipQDb8yBJ-N67fl2', 'CBJCHBCAABAA7LD6DA_vq_Vq8lb32LZCWXI9fyz8Hv76', 'CBJCHBCAABAARwsZrkmL4K9zlsaGV2hN2eAUFrc8A81F', 'CBJCHBCAABAA0lOKADYSJWi5eUputD6UkUwBjmD5K3Gm', 'CBJCHBCAABAAnTeZShsLfjAw9bBD6dsRWzF2DUB5A4xS', 'CBJCHBCAABAAhvjnpFlz1V3agZK8xTmnvZh5IY5FeJcV', 'CBJCHBCAABAA5McBKomQbyTe2om4NBHCHOZOxWVNmkh4', 'CBJCHBCAABAADDTfBZotL-WDcMx6DSe60nY-ATEy3Y66', 'CBJCHBCAABAAQzg_idagWrkTNEL7o0q1wbvbkqqgQvd1', 'CBJCHBCAABAAOB8OjkJnDmQgmrt0kztN9KRxZowvPKSu', 'CBJCHBCAABAAGlgf_7Ez7AJ0qHfizjHTBeKhEWPM45Df', 'CBJCHBCAABAASN-mE0Aj5t3wPe8H7GNbEO8ZNWTmsHLo', 'CBJCHBCAABAAx6-2gwY398VJ3HdlmCGPelKsvg7z37wf', 'CBJCHBCAABAAc-MpF4EjlYCx02rtYm9pc18JjN1FAG0J', 'CBJCHBCAABAAFImSTglGhsmGr4V3ouSFSFyV4NxtQ6hT']


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
9. 1570 - EDGE CASE - toma el 2025 como Cuenta Contable - CBJCHBCAABAAYARob0IVL0UhIPKxTshuZW-IkfAVKWyZ
10. 2368 - CBJCHBCAABAAsCMMrkMsddLn_pdWXoAjIxk4_SVXZ0fs
11. 3165 - CBJCHBCAABAAkjBy--jGnJzRpIebK5qHx4r8JT1JIzQF

## edge cases
6. 885 - CBJCHBCAABAALuqZmF8io5IxI_J7RaZ6jOa027m_vVkP - No encuentra RUT - 3 x Centro de Costos, Cuenta Contable, Orden controlling
  * borraron 'soial' del doc, acortar la lsita de anchors
  * 
7. 889 - CBJCHBCAABAAU7IoQdZRsYlcYMIiP24XOsnEu8R48Ycl - Sin Gerencia solicitante.
  * agregar get (, "NO ESPECIFICA") o VAR {NOT_FOUND}
9. 1570 - EDGE CASE - toma el 2025 como Cuenta Contable - CBJCHBCAABAAYARob0IVL0UhIPKxTshuZW-IkfAVKWyZ
  * correr la busqueda de anchor al final y restar index ('Completar', 'todos', 'los', 'campos', 'del', 'documento.')
  
## PENDING
* mecanismo de validacion para casos manuales (3 x cta contable)


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
