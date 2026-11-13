"""Valida BPMN 2.0 con XSD oficial y comprobaciones de grafo/DI.

Uso: python validar_diagramas.py --schema-dir ruta/a/esquemas_OMG
Descargar BPMN20.xsd, BPMNDI.xsd, DC.xsd, DI.xsd y Semantic.xsd
desde https://www.omg.org/spec/BPMN/20100501/ en la misma carpeta.
"""
from pathlib import Path
from lxml import etree as E
import argparse, json

NS={'b':'http://www.omg.org/spec/BPMN/20100524/MODEL','bd':'http://www.omg.org/spec/BPMN/20100524/DI','dc':'http://www.omg.org/spec/DD/20100524/DC','di':'http://www.omg.org/spec/DD/20100524/DI'}
OUT=Path(__file__).resolve().parent
def validate(path,schema=None):
 tree=E.parse(str(path));root=tree.getroot();errors=[]
 if schema is not None:
  if not schema.validate(tree): errors += ['XSD: '+str(x) for x in schema.error_log]
 ids=[x.get('id') for x in root.iter() if x.get('id')]
 if len(ids)!=len(set(ids)):errors.append('ID duplicado')
 byid={x.get('id'):x for x in root.iter() if x.get('id')}
 process=root.find('b:process',NS)
 nodes={n.get('id'):n for n in process if E.QName(n).localname in {'startEvent','endEvent','task','subProcess','exclusiveGateway'}}
 flows=process.findall('b:sequenceFlow',NS)
 incoming={id:[] for id in nodes};outgoing={id:[] for id in nodes}
 for f in flows:
  s,t=f.get('sourceRef'),f.get('targetRef')
  if s not in nodes or t not in nodes:errors.append('Extremo de secuencia no válido: '+f.get('id'));continue
  incoming[t].append(f.get('id'));outgoing[s].append(f.get('id'))
 for id,n in nodes.items():
  typ=E.QName(n).localname
  if typ!='startEvent' and not incoming[id]:errors.append('Nodo sin entrada: '+id)
  if typ!='endEvent' and not outgoing[id]:errors.append('Nodo sin salida: '+id)
  if typ=='exclusiveGateway' and len(outgoing[id])>1:
   for fid in outgoing[id]:
    if not byid[fid].get('name') or byid[fid].find('b:conditionExpression',NS) is None:errors.append('Decisión sin condición: '+fid)
  for direction,expected in [('incoming',incoming[id]),('outgoing',outgoing[id])]:
   actual=[x.text for x in n.findall('b:'+direction,NS)]
   if sorted(actual)!=sorted(expected):errors.append('Referencias '+direction+' incoherentes: '+id)
 starts=[id for id,n in nodes.items() if E.QName(n).localname=='startEvent']
 ends={id for id,n in nodes.items() if E.QName(n).localname=='endEvent'}
 def reachable(seeds,reverse=False):
  found=set(seeds); changed=True
  while changed:
   changed=False
   for f in flows:
    s,t=(f.get('targetRef'),f.get('sourceRef')) if reverse else (f.get('sourceRef'),f.get('targetRef'))
    if s in found and t not in found:found.add(t);changed=True
  return found
 if set(nodes)-reachable(starts):errors.append('Nodos no alcanzables desde inicio')
 if set(nodes)-reachable(ends,True):errors.append('Nodos sin ruta a fin')
 lanes=process.findall('b:laneSet/b:lane',NS)
 assigned=[r.text for l in lanes for r in l.findall('b:flowNodeRef',NS)]
 if sorted(assigned)!=sorted(nodes):errors.append('Asignación de carriles incompleta o duplicada')
 shapes={s.get('bpmnElement'):s for s in root.findall('.//bd:BPMNShape',NS)}
 for l in lanes:
  b=shapes[l.get('id')].find('dc:Bounds',NS);top=float(b.get('y'));bottom=top+float(b.get('height'))
  for ref in l.findall('b:flowNodeRef',NS):
   bb=shapes[ref.text].find('dc:Bounds',NS);y=float(bb.get('y'));h=float(bb.get('height'))
   if y<top or y+h>bottom:errors.append('Nodo fuera de su carril: '+ref.text)
 participants={n.get('id') for n in root.findall('b:collaboration/b:participant',NS)}
 for m in root.findall('b:collaboration/b:messageFlow',NS):
  s,t=m.get('sourceRef'),m.get('targetRef')
  if s not in byid or t not in byid:errors.append('Mensaje no resuelto: '+m.get('id'))
  if not ((s in participants) ^ (t in participants)):errors.append('Mensaje no cruza participante: '+m.get('id'))
 for edge in root.findall('.//bd:BPMNEdge',NS):
  if edge.get('bpmnElement') not in byid:errors.append('DI sin elemento')
  if len(edge.findall('di:waypoint',NS))<2:errors.append('Arista sin coordenadas')
 for ext in ('.svg','.png'):
  if not path.with_suffix(ext).exists():errors.append('Exportación faltante '+ext)
 return {'archivo':path.name,'xsd_OMG':schema is not None,'nodos_principales':len(nodes),'secuencias':len(flows),'mensajes':len(root.findall('b:collaboration/b:messageFlow',NS)),'errores':errors}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--schema-dir',type=Path);p.add_argument('--output',type=Path);args=p.parse_args()
 schema=E.XMLSchema(E.parse(str(args.schema_dir/'BPMN20.xsd'))) if args.schema_dir else None
 result=[validate(p,schema) for p in sorted(OUT.glob('*.bpmn'))]
 text=json.dumps(result,ensure_ascii=False,indent=2)
 print(text)
 if args.output:args.output.write_text(text+'\n',encoding='utf8')
 if any(r['errores'] for r in result):raise SystemExit(1)
