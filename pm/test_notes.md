# Test Log

## JAD WF 6 OK
1. 759 - CBJCHBCAABAA-t9NJfmwxJgPZby4BpezQ256Q9koTDUY
2. 766 - CBJCHBCAABAA_AL2p5mrLyksv7oY8HhlyMPb5AbhSGIq
3. 767 - CBJCHBCAABAABs5JwBWb2JaSHApcbwicD-THKQ7oOL_m
4. 801 - CBJCHBCAABAApLxW-kW-a_LC9UClFxVcRt4ZpbPVoKbT
5. 871 - CBJCHBCAABAAke5ku2eEH_jR2UAjuKcuVT8az2uMe6EI
8. 1195 - CBJCHBCAABAAcAOdafnz8yPeKgzhedX3UXBrm16_HqI4
10. 2368 - CBJCHBCAABAAsCMMrkMsddLn_pdWXoAjIxk4_SVXZ0fs
11. 3165 - CBJCHBCAABAAkjBy--jGnJzRpIebK5qHx4r8JT1JIzQF

## JAD WF 6 EDGE CASE
6. 885 - EDGE CASE - No encuentra RUT
7. 889 - EDGE CASE - gerenncia_solicitante= None
9. 1570 - EDGE CASE - toma el 2025 como Cuenta Contable - CBJCHBCAABAAYARob0IVL0UhIPKxTshuZW-IkfAVKWyZ

## JAD WF 6 EDGE CASE FIX
6. 885 - CBJCHBCAABAALuqZmF8io5IxI_J7RaZ6jOa027m_vVkP - No encuentra RUT - 3 x Centro de Costos, Cuenta Contable, Orden controlling
  * borraron 'soial' del doc, acortar la lsita de anchors

7. 889 - CBJCHBCAABAAU7IoQdZRsYlcYMIiP24XOsnEu8R48Ycl - Sin Gerencia solicitante.
  * agregar get (, "NO ESPECIFICA") o VAR {NOT_FOUND}
9. 1570 - EDGE CASE - toma el 2025 como Cuenta Contable - CBJCHBCAABAAYARob0IVL0UhIPKxTshuZW-IkfAVKWyZ
  * correr la busqueda de anchor al final y restar index ('Completar', 'todos', 'los', 'campos', 'del', 'documento.')
  
## PENDING
* mecanismo de validacion para casos manuales (3 x cta contable)
