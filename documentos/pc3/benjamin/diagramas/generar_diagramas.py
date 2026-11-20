"""Fuentes editables y exportación SVG de la cadena de suministro PC3.

Python 3 + lxml. Los PNG se exportan con sharp en exportar_png.cjs.
Cada SVG de proceso y su BPMN DI proceden del mismo modelo geométrico.
"""
from pathlib import Path
from html import escape
import textwrap
from lxml import etree as E

OUT=Path(__file__).resolve().parent
NS={'bpmn':'http://www.omg.org/spec/BPMN/20100524/MODEL','bpmndi':'http://www.omg.org/spec/BPMN/20100524/DI','dc':'http://www.omg.org/spec/DD/20100524/DC','di':'http://www.omg.org/spec/DD/20100524/DI','xsi':'http://www.w3.org/2001/XMLSchema-instance'}
BLUE='#244b72'; TEAL='#087f8c'; GREY='#637382'; PALE='#eef4fa'; GOLD='#986816'
def q(p,n): return '{'+NS[p]+'}'+n
def el(p,n,**a): return E.Element(q(p,n),{k:str(v) for k,v in a.items()})

class Svg:
 def __init__(self,w,h,title,subtitle):
  self.w,self.h=w,h
  self.s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">',f'<defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 Z" fill="{BLUE}"/></marker><marker id="info" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8" fill="none" stroke="{TEAL}" stroke-width="1.5"/></marker><marker id="messageStart" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><circle cx="4" cy="4" r="2.5" fill="white" stroke="{TEAL}" stroke-width="1"/></marker><marker id="money" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 Z" fill="{GREY}"/></marker></defs>','<rect width="100%" height="100%" fill="white"/>']
  self.text(42,48,title,30,BLUE,False)
  self.text(42,83,subtitle,20,GREY,False)
 def text(self,x,y,t,size=21,color=BLUE,center=True,width=None):
  lines=[]
  for line in t.split('\n'):
   lines.extend(textwrap.wrap(line,width=max(8,int(width/(size*.50)))) if width else [line])
  for i,l in enumerate(lines): self.s.append(f'<text x="{x}" y="{y+i*size*1.23:.1f}" font-family="Arial, sans-serif" font-size="{size}" fill="{color}" text-anchor="{"middle" if center else "start"}">{escape(l)}</text>')
 def box(self,x,y,w,h,t,fill=PALE,stroke=BLUE,dash=None,size=21):
  ds=f' stroke-dasharray="{dash}"' if dash else ''
  self.s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"{ds}/>')
  while True:
   lines=[]
   for l in t.split('\n'): lines.extend(textwrap.wrap(l,width=max(8,int((w-24)/(size*.50)))))
   if len(lines)*size*1.23 <= h-12 or size<=18:break
   size-=.5
  self.text(x+w/2,y+(h-len(lines)*size*1.23)/2+size,'\n'.join(lines),size,stroke)
 def line(self,pts,label='',kind='seq',lx=None,ly=None):
  color={'seq':BLUE,'info':TEAL,'msg':TEAL,'money':GREY,'assoc':GREY}[kind]
  dash=' stroke-dasharray="9 6"' if kind in ('info','msg','assoc') else ''
  marker=f' marker-end="url(#{"info" if kind in ("info","msg") else "money" if kind=="money" else "arrow"})"' if kind!='assoc' else ''
  if kind=='msg':
   self.s.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="white" stroke-width="6"/>')
   marker+=' marker-start="url(#messageStart)"'
  self.s.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="{color}" stroke-width="{2 if kind=="money" else 2.5}"{dash}{marker}/>')
  if label:
   x,y=(lx,ly) if lx is not None else ((pts[0][0]+pts[-1][0])/2,(pts[0][1]+pts[-1][1])/2-10)
   # A white backing makes labels readable where lines run behind them.
   tw=max(len(l) for l in label.split('\n'))*10.3
   self.s.append(f'<rect x="{x-tw/2-5}" y="{y-20}" width="{tw+10}" height="{len(label.split(chr(10)))*25}" fill="white"/>')
   self.text(x,y,label,19,color)
 def save(self,name):
  (OUT/(name+'.svg')).write_text('\n'.join(self.s+['</svg>']),encoding='utf8')

class Model:
 def __init__(self,name,title,subtitle,lanes,pools,w=1660,h=930):
  self.name=name; self.title=title; self.lanes=lanes; self.pools=pools; self.nodes={}; self.flows=[]; self.messages=[]; self.assocs=[]; self.data=[]; self.edge_labels={}
  self.svg=Svg(w,h,title,subtitle)
  # Pools and lanes share a common geometry with BPMN DI.
  for i,(lid,label,y,hh) in enumerate(lanes):
   self.svg.s.append(f'<rect x="40" y="{y}" width="{w-80}" height="{hh}" fill="{"#f5f8fc" if i%2==0 else "white"}" stroke="#9aabbc" stroke-width="1.5"/>')
   self.svg.s.append(f'<rect x="40" y="{y}" width="82" height="{hh}" fill="#e3edf6" stroke="#9aabbc"/>')
   self.svg.s.append(f'<g transform="translate(88 {y+hh/2}) rotate(-90)">')
   lane_lines=textwrap.wrap(label,width=max(9,int((hh-24)/10.5)))
   self.svg.text(0,-8 if len(lane_lines)>1 else 7,'\n'.join(lane_lines),21,BLUE)
   self.svg.s.append('</g>')
  for pid,label,x,y,ww,hh in pools:
   self.svg.s.append(f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" fill="#f2f3f4" stroke="{GREY}" stroke-width="2"/>')
   self.svg.text(x+ww/2,y+hh/2+7,label,21,GREY)
 def node(self,id,typ,name,lane,x,y,w=180,h=84,label_dx=0,label_dy=None):
  if typ in ('startEvent','endEvent'): w=h=38
  if typ=='exclusiveGateway': w=h=52
  self.nodes[id]={'typ':typ,'name':name,'lane':lane,'x':x,'y':y,'w':w,'h':h}
  s=self.svg
  if typ in ('startEvent','endEvent'):
   s.s.append(f'<circle cx="{x+w/2}" cy="{y+h/2}" r="{w/2-2}" fill="white" stroke="{BLUE}" stroke-width="{4 if typ=="endEvent" else 2}"/>')
   event_dx=35 if typ=='startEvent' and not label_dx else label_dx
   label_cx=x+w/2+event_dx
   label_y=y+h+(45 if typ=='startEvent' else 25) if label_dy is None else y+label_dy
   label_w=130 if typ=='startEvent' else 155
   label_lines=textwrap.wrap(name,width=int(label_w/9.5))
   self.nodes[id]['label_bounds']=(label_cx-label_w/2,label_y-19,label_w,len(label_lines)*23.37)
   s.text(label_cx,label_y,name,19,BLUE,width=label_w)
  elif typ=='exclusiveGateway':
   s.s.append(f'<path d="M{x+w/2},{y} L{x+w},{y+h/2} L{x+w/2},{y+h} L{x},{y+h/2} Z" fill="#fff6e8" stroke="{GOLD}" stroke-width="2"/>')
   s.text(x+w/2,y+h/2+7,'×',29,GOLD)
   lines=textwrap.wrap(name,width=18)
   label_cx=x+w/2+label_dx
   label_y=(y-18-(len(lines)-1)*24.6) if label_dy is None else y+label_dy
   label_w=max(len(l) for l in lines)*10+8
   self.nodes[id]['label_bounds']=(label_cx-label_w/2,label_y-20,label_w,len(lines)*24.6)
   s.text(label_cx,label_y,'\n'.join(lines),20,BLUE)
  else:
   s.box(x,y,w,h,name,size=21)
   if typ=='subProcess':
    s.s.append(f'<rect x="{x+w/2-7}" y="{y+h-17}" width="14" height="14" fill="white" stroke="{BLUE}"/>')
    s.text(x+w/2,y+h-5,'+',15,BLUE)
  return id
 def flow(self,src,tgt,pts,label='',lx=None,ly=None):
  self._edge_label('Flow_'+str(len(self.flows)),pts,label,lx,ly)
  self.flows.append((src,tgt,pts,label));self.svg.line(pts,label,'seq',lx,ly)
 def msg(self,src,tgt,pts,label='',lx=None,ly=None):
  self._edge_label('Message_'+str(len(self.messages)),pts,label,lx,ly)
  self.messages.append((src,tgt,pts,label));self.svg.line(pts,label,'msg',lx,ly)
 def _edge_label(self,id,pts,label,lx,ly):
  if not label:return
  x,y=(lx,ly) if lx is not None else ((pts[0][0]+pts[-1][0])/2,(pts[0][1]+pts[-1][1])/2-10)
  width=max(len(l) for l in label.split('\n'))*10.3
  self.edge_labels[id]=(x-width/2,y-19,width,len(label.split('\n'))*25)
 def datum(self,id,name,x,y,w=150,h=62,target=None,pts=None):
  self.data.append((id,name,x,y,w,h));s=self.svg
  s.s.append(f'<path d="M{x},{y} H{x+w-20} L{x+w},{y+20} V{y+h} H{x} Z M{x+w-20},{y} V{y+20} H{x+w}" fill="#fffdf6" stroke="{GREY}" stroke-width="1.5"/>')
  s.text(x+w/2,y+25,name,19,GREY,width=w-12)
  if target: self.assocs.append((id,target,pts));s.line(pts,kind='assoc')
 def note(self,x,y,w,t):
  lines=[]
  for l in t.split('\n'): lines.extend(textwrap.wrap(l,width=int(w/10)))
  self.svg.text(x,y,'\n'.join(lines),19,GREY,False)
 def save(self):
  self.svg.save(self.name)
  root=E.Element(q('bpmn','definitions'),nsmap=NS,id='Definitions_'+self.name,targetNamespace='https://github.com/jharopr/ERP-SIE/pc3/benjamin')
  process=E.SubElement(root,q('bpmn','process'),id='Process_MYS',name=self.title,isExecutable='false')
  ls=E.SubElement(process,q('bpmn','laneSet'),id='LaneSet_MYS')
  for lid,label,y,hh in self.lanes:
   lane=E.SubElement(ls,q('bpmn','lane'),id=lid,name=label)
   for id,n in self.nodes.items():
    if n['lane']==lid: E.SubElement(lane,q('bpmn','flowNodeRef')).text=id
  for id,n in self.nodes.items():
   node=E.SubElement(process,q('bpmn',n['typ']),id=id,name=n['name'].replace('\n',' '))
   for i,(src,tgt,pts,label) in enumerate(self.flows):
    if tgt==id:E.SubElement(node,q('bpmn','incoming')).text='Flow_'+str(i)
   for i,(src,tgt,pts,label) in enumerate(self.flows):
    if src==id:E.SubElement(node,q('bpmn','outgoing')).text='Flow_'+str(i)
   # A collapsed subprocess contains an explicit start/task/end. It is a
   # non-executable analytical detail, rather than an empty opaque activity.
   if n['typ']=='subProcess':
    E.SubElement(node,q('bpmn','startEvent'),id=id+'_start')
    E.SubElement(node,q('bpmn','task'),id=id+'_detail',name='Evaluación humana y seguimiento según sección 5B')
    E.SubElement(node,q('bpmn','endEvent'),id=id+'_end')
    E.SubElement(node,q('bpmn','sequenceFlow'),id=id+'_f1',sourceRef=id+'_start',targetRef=id+'_detail')
    E.SubElement(node,q('bpmn','sequenceFlow'),id=id+'_f2',sourceRef=id+'_detail',targetRef=id+'_end')
  for i,(src,tgt,pts,label) in enumerate(self.flows):
   a={'id':'Flow_'+str(i),'sourceRef':src,'targetRef':tgt}
   if label:a['name']=label.replace('\n',' ')
   fl=E.SubElement(process,q('bpmn','sequenceFlow'),**a)
   if self.nodes[src]['typ']=='exclusiveGateway':
    cond=E.SubElement(fl,q('bpmn','conditionExpression'));cond.set(q('xsi','type'),'bpmn:tFormalExpression');cond.text=label or 'Ruta documentada'
  for id,name,x,y,w,h in self.data:
   E.SubElement(process,q('bpmn','dataObject'),id=id+'_object')
   E.SubElement(process,q('bpmn','dataObjectReference'),id=id,name=name.replace('\n',' '),dataObjectRef=id+'_object')
  for i,(src,tgt,pts) in enumerate(self.assocs): E.SubElement(process,q('bpmn','association'),id='Assoc_'+str(i),sourceRef=src,targetRef=tgt,associationDirection='None')
  coll=E.SubElement(root,q('bpmn','collaboration'),id='Collaboration')
  E.SubElement(coll,q('bpmn','participant'),id='Participant_MYS',name='Importaciones MYS Hermanos S A C',processRef='Process_MYS')
  for pid,label,x,y,w,h in self.pools:E.SubElement(coll,q('bpmn','participant'),id=pid,name=label)
  for i,(src,tgt,pts,label) in enumerate(self.messages):E.SubElement(coll,q('bpmn','messageFlow'),id='Message_'+str(i),sourceRef=src,targetRef=tgt,name=label.replace('\n',' '))
  d=E.SubElement(root,q('bpmndi','BPMNDiagram'),id='Diagram_'+self.name)
  plane=E.SubElement(d,q('bpmndi','BPMNPlane'),id='Plane',bpmnElement='Collaboration')
  def shape(id,ref,x,y,w,h,**attrs):
   sh=E.SubElement(plane,q('bpmndi','BPMNShape'),id=id,bpmnElement=ref,**attrs);E.SubElement(sh,q('dc','Bounds'),x=str(x),y=str(y),width=str(w),height=str(h))
   return sh
  def add_label(parent,bounds):
   x,y,w,h=bounds;lab=E.SubElement(parent,q('bpmndi','BPMNLabel'));E.SubElement(lab,q('dc','Bounds'),x=str(x),y=str(y),width=str(w),height=str(h))
  y0=self.lanes[0][2]; yend=self.lanes[-1][2]+self.lanes[-1][3]
  shape('DI_MYS','Participant_MYS',40,y0,self.svg.w-80,yend-y0,isHorizontal='true')
  for lid,label,y,h in self.lanes:shape('DI_'+lid,lid,40,y,self.svg.w-80,h,isHorizontal='true')
  for pid,label,x,y,w,h in self.pools:shape('DI_'+pid,pid,x,y,w,h,isHorizontal='true')
  for id,n in self.nodes.items():
   sh=shape('DI_'+id,id,n['x'],n['y'],n['w'],n['h'],**({'isExpanded':'false'} if n['typ']=='subProcess' else {}))
   if 'label_bounds' in n:add_label(sh,n['label_bounds'])
  for id,name,x,y,w,h in self.data:
   sh=shape('DI_'+id,id,x,y,w,h);add_label(sh,(x+6,y+6,w-12,h-12))
  for prefix,items in [('Flow',self.flows),('Message',self.messages),('Assoc',[(s,t,p,'') for s,t,p in self.assocs])]:
   for i,(src,tgt,pts,label) in enumerate(items):
    edge=E.SubElement(plane,q('bpmndi','BPMNEdge'),id='DI_'+prefix+'_'+str(i),bpmnElement=prefix+'_'+str(i))
    for x,y in pts:E.SubElement(edge,q('di','waypoint'),x=str(x),y=str(y))
    if prefix+'_'+str(i) in self.edge_labels:add_label(edge,self.edge_labels[prefix+'_'+str(i)])
  (OUT/(self.name+'.bpmn')).write_bytes(E.tostring(root,xml_declaration=True,encoding='UTF-8',pretty_print=True))

def integral():
 s=Svg(1780,1120,'Figura 1  Red de abastecimiento de MYS','Canal de evaluación: clientes nuevos del público general en tiendas físicas')
 # Product layer and core nodes.
 s.box(40,150,355,106,'GUANGDONG XUYING\nHuizhou · mercancía no especificada [P1]',size=22)
 s.box(40,280,355,106,'MEICANXIN (HK)\nDirección Shenzhen · multimedia negociada [P2]',size=22)
 s.box(40,410,355,106,'SHENZHEN GEARFORCE\nMultimedia y cámaras negociadas [P3]',size=22)
 s.box(460,270,235,120,'Importación y aduanas\nOperadores no identificados [S2]',size=22)
 s.box(755,335,280,155,'Carabayllo\nN1 audio y pantallas\nN2 adaptación y cables\nAlmacenero fijo [S1]',size=23)
 s.box(1095,365,220,126,'inDrive mayoritario\nTraslado interno [S1]',size=22)
 s.box(1380,245,345,112,'Tienda 1 · La 50\n3 espacios utilizables\nEncargado familiar [S1]',size=23)
 s.box(1380,495,345,112,'Tienda 2 · La 50\n1 espacio utilizable\nEncargado familiar [S1]',size=23)
 s.box(1375,700,350,98,'Clientes presenciales\nCompra y posible instalación',size=23)
 s.box(740,115,330,130,'Gestión familiar\nDecisión de compra\nExperiencia familiar\nCuaderno y Excel',fill='#e9f6f5',stroke=TEAL,size=22)
 s.box(1095,625,220,92,'Trimoto propia\nReparto y gestiones',size=21)
 # Core solid product paths.
 for y in (203,333,463):s.line([(395,y),(428,y),(428,330),(460,330)])
 s.line([(695,330),(723,330),(723,412),(755,412)],'Transporte pesado\ncontratado',lx=607,ly=454)
 s.line([(1035,412),(1095,412)])
 s.line([(1315,412),(1344,412),(1344,301),(1380,301)])
 s.line([(1315,430),(1344,430),(1344,551),(1380,551)])
 s.line([(1552,357),(1552,435),(1745,435),(1745,745),(1725,745)])
 s.line([(1552,607),(1552,700)])
 s.line([(1380,570),(1355,570),(1355,667),(1315,667)],kind='info')
 # Feedback / purchasing information uses an upper/lower corridor.
 s.line([(1470,245),(1470,115),(1070,115),(1070,168)],'Solicitudes y ventas',kind='info',lx=1270,ly=105)
 s.line([(1380,520),(1070,520),(1070,245),(1042,245)],'Faltantes y demanda',kind='info',lx=1210,ly=546)
 s.line([(895,245),(895,335)],'Necesidad\nde compra',kind='info',lx=1000,ly=280)
 s.line([(740,165),(420,165),(420,120),(205,120),(205,150)],'Condiciones y decisión de abastecimiento',kind='info',lx=455,ly=132)
 s.line([(740,208),(708,208),(708,554),(200,554),(200,530)],'Compromisos de compra y pagos',kind='money',lx=505,ly=545)
 s.text(200,585,'Flujo económico representativo\nal conjunto de proveedores',18,GREY)
 # Local alternative and potential reference are explicitly segregated.
 s.box(40,655,610,157,'Referencia comercial externa [P4]\nDong Guan Shi Huang Jiang Jie Hang Dian Zi Shang Hang\nFactura a IMPORTACIONES SOTMA S.A.C.\nNo acredita una relación comercial con MYS',fill='#fffdf6',stroke=GOLD,dash='8 6',size=22)
 s.box(740,785,570,105,'Proveedores locales de arnés / Canbus\nSin razón social identificada · antecedente de urgencia [S1]',fill='#fffdf6',stroke=GOLD,dash='8 6',size=23)
 s.line([(1310,837),(1350,837),(1350,600),(1380,600)],'Alternativa por validar',kind='info',lx=1490,ly=854)
 s.text(42,945,'Leyenda',23,BLUE,False)
 s.line([(170,939),(275,939)]);s.text(290,946,'Producto y materiales',21,BLUE,False)
 s.line([(660,939),(765,939)],kind='info');s.text(780,946,'Información y decisiones',21,TEAL,False)
 s.line([(1230,939),(1335,939)],kind='money');s.text(1350,946,'Compromiso económico',21,GREY,False)
 s.text(42,994,'Vínculos comerciales documentados en 2025; vigencia y ruta específica por confirmar. Las referencias negociadas no prueban recepción ni stock.',20,GREY,False)
 s.text(42,1024,'No se identificó por nombre un proveedor nacional de mercancía. Las rutas a provincias son contexto secundario; se evalúa la atención presencial.',20,GREY,False)
 s.text(42,1066,'Fuentes: S1 Adrián 5A; S2 Adrián 5C; P1–P4 documentos empresariales suministrados. Elaboración para PC3 · 12/11/2026.',20,GREY,False)
 s.save('01_red_integral')

def international():
 m=Model('02_asis_internacional','Figura 2  Abastecimiento internacional AS IS','Reconstrucción analítica de la práctica declarada; no acredita un procedimiento formal vigente.',[('Lane_Familia','Gestión familiar',150,270),('Lane_Almacen','Almacenero fijo',420,250)],[('Pool_Proveedor','Proveedor internacional · participante externo',40,735,745,70),('Pool_Logistica','Logística de importación · operador no identificado',845,735,775,70)])
 m.node('Inicio','startEvent','Necesidad de abastecer','Lane_Familia',150,250)
 m.node('Identificar','task','Identificar necesidades','Lane_Familia',220,225,170,90)
 m.node('Revisar','task','Revisar experiencia y registros','Lane_Familia',435,225,185,90)
 m.node('Evaluar','task','Considerar proveedor y condiciones','Lane_Familia',665,225,190,90)
 m.node('Decidir','exclusiveGateway','¿Comprar?','Lane_Familia',900,244)
 m.node('Comprar','subProcess','Decidir pedido y coordinar importación','Lane_Familia',1010,225,230,100)
 m.node('Recibir','task','Recibir mercadería en Carabayllo','Lane_Almacen',1330,480,205,95)
 m.node('Fin','endEvent','Recibida','Lane_Almacen',1560,510)
 m.node('Postergar','task','Postergar la compra','Lane_Familia',805,335,190,65)
 m.node('FinPendiente','endEvent','Pendiente','Lane_Familia',1080,335)
 m.flow('Inicio','Identificar',[(188,269),(220,269)])
 m.flow('Identificar','Revisar',[(390,269),(435,269)])
 m.flow('Revisar','Evaluar',[(620,269),(665,269)])
 m.flow('Evaluar','Decidir',[(855,269),(900,269)])
 m.flow('Decidir','Comprar',[(952,270),(1010,270)],'Sí',lx=980,ly=254)
 m.flow('Decidir','Postergar',[(926,296),(926,318),(900,318),(900,335)],'No',lx=960,ly=328)
 m.flow('Postergar','FinPendiente',[(995,368),(1040,368),(1040,354),(1080,354)])
 m.flow('Comprar','Recibir',[(1240,272),(1280,272),(1280,528),(1330,528)])
 m.flow('Recibir','Fin',[(1535,528),(1560,528)])
 m.datum('Registros','Cuaderno y Excel',440,340,180,58,'Revisar',[(530,340),(530,315)])
 m.msg('Comprar','Pool_Proveedor',[(1210,325),(1210,700),(405,700),(405,735)],'Pedido / condiciones',lx=655,ly=690)
 m.msg('Pool_Logistica','Recibir',[(1450,735),(1450,575)],'Aviso de arribo',lx=1500,ly=650)
 m.note(42,850,1570,'Brecha: no se aportaron plazos completos, cantidades conciliadas ni expediente enlazado de compra–importación–recepción. La decisión sigue siendo humana. Fuentes S1 y S2; notación BPMN 2.0.2 (OMG).')
 m.save()

def internal():
 m=Model('03_asis_reposicion','Figura 3  Reposición interna AS IS','Carabayllo → tiendas de La 50. La recepción está declarada; su control de conformidad no fue descrito.',[('Lane_Tienda','Encargado de tienda',150,180),('Lane_Almacen','Almacenero fijo',330,205),('Lane_Familia','Gestión familiar',535,180)],[('Pool_Transporte','Transporte externo · mayoritariamente inDrive',40,770,1580,70)])
 m.node('Inicio','startEvent','Necesidad en tienda','Lane_Tienda',145,215)
 m.node('Anotar','task','Anotar necesidad en cuaderno','Lane_Tienda',215,190,200,90)
 m.node('Coordinar','task','Coordinar reposición','Lane_Familia',445,575,195,90)
 m.node('Revisar','task','Revisar mercadería para preparar','Lane_Almacen',690,375,190,90)
 m.node('Disponible','exclusiveGateway','¿Se puede reponer?','Lane_Almacen',930,394)
 m.node('Preparar','task','Preparar mercadería y coordinar traslado','Lane_Almacen',1040,375,220,100)
 m.node('Recibir','task','Recibir en tienda','Lane_Tienda',1350,190,195,90)
 m.node('Fin','endEvent','Recibida','Lane_Tienda',1570,218)
 m.node('Pendiente','task','Mantener necesidad para decisión familiar','Lane_Familia',875,575,250,90)
 m.node('FinPendiente','endEvent','Atención por resolver','Lane_Familia',1190,600)
 m.flow('Inicio','Anotar',[(183,234),(215,234)])
 m.flow('Anotar','Coordinar',[(415,234),(430,234),(430,620),(445,620)])
 m.flow('Coordinar','Revisar',[(640,620),(665,620),(665,420),(690,420)])
 m.flow('Revisar','Disponible',[(880,420),(930,420)])
 m.flow('Disponible','Preparar',[(982,420),(1040,420)],'Sí',lx=1010,ly=405)
 m.flow('Disponible','Pendiente',[(956,446),(956,575)],'No',lx=981,ly=505)
 m.flow('Pendiente','FinPendiente',[(1125,620),(1190,620)])
 m.flow('Preparar','Recibir',[(1260,420),(1310,420),(1310,235),(1350,235)])
 m.flow('Recibir','Fin',[(1545,235),(1570,235)])
 m.datum('Cuaderno','Cuaderno de necesidades',215,342,195,65,'Anotar',[(310,342),(310,280)])
 m.msg('Preparar','Pool_Transporte',[(1160,475),(1160,510),(1320,510),(1320,735),(530,735),(530,770)],'Coordinación del traslado',lx=800,ly=725)
 m.msg('Pool_Transporte','Recibir',[(1450,770),(1450,280)],'Aviso / entrega',lx=1515,ly=680)
 m.note(42,888,1570,'Reconstrucción analítica: la alternativa sin mercadería resume una decisión aún no formalizada. No se atribuyen al cuaderno campos o trazas no inspeccionados. Fuentes S1 y S2. Línea continua: secuencia; discontinua: mensaje; hoja: datos.')
 m.save()

def future():
 m=Model('04_tobe_reposicion','Figura 4  Reposición TO BE con trazabilidad','Diseño propuesto. Una compra autorizada no equivale a mercadería disponible; los faltantes conservan seguimiento.',[('Lane_Tienda','Encargado de tienda',115,240),('Lane_Almacen','Almacenero fijo',355,245),('Lane_Familia','Propietarios',600,230)],[('Pool_Transporte','Transportista externo · confirmación de recojo y entrega',40,885,1720,65)],w=1800,h=1110)
 m.node('Inicio','startEvent','Necesidad identificada','Lane_Tienda',145,228)
 m.node('Solicitar','task','Crear solicitud ID, SKU, cantidad y fecha','Lane_Tienda',215,205,210,100)
 m.node('Referencia','exclusiveGateway','¿Referencia compatible?','Lane_Tienda',470,225,label_dy=-39)
 m.node('Aclarar','task','Aclarar referencia y compatibilidad','Lane_Tienda',665,205,180,90)
 m.node('Verificar','task','Verificar existencia y saldo por ubicación','Lane_Almacen',465,400,220,100)
 m.node('Hay','exclusiveGateway','¿Saldo suficiente?','Lane_Almacen',735,424)
 m.node('Preparar','task','Preparar y confirmar referencias / cantidades','Lane_Almacen',845,400,210,100)
 m.node('Despachar','task','Registrar salida y tránsito','Lane_Almacen',1105,400,195,100)
 m.node('Recibir','task','Cotejar y registrar recepción','Lane_Tienda',1330,205,195,100)
 m.node('Conforme','exclusiveGateway','¿Coincide?','Lane_Tienda',1570,228,label_dx=75,label_dy=16)
 m.node('Cerrar','task','Cerrar y actualizar saldos','Lane_Tienda',1600,125,160,85)
 m.node('Fin','endEvent','Cerrada','Lane_Tienda',1710,272)
 m.node('Diferencia','task','Registrar diferencia y conciliar con tienda','Lane_Almacen',1480,400,240,100)
 m.node('FinDiferencia','endEvent','Por conciliar','Lane_Almacen',1700,525)
 m.node('Faltante','task','Registrar saldo no atendido y evaluar compra','Lane_Familia',640,650,230,100)
 m.node('Autorizar','exclusiveGateway','¿Autorizar compra?','Lane_Familia',940,675)
 m.node('Compra','subProcess','Gestionar compra y seguimiento de recepción','Lane_Familia',1080,650,240,110)
 m.node('FinCompra','endEvent','Necesidad en seguimiento','Lane_Familia',1520,682)
 m.node('FinNoCompra','endEvent','Sin compra','Lane_Familia',970,765)
 m.flow('Inicio','Solicitar',[(183,247),(215,247)])
 m.flow('Solicitar','Referencia',[(425,251),(470,251)])
 m.flow('Referencia','Aclarar',[(522,251),(665,251)],'No / duda',lx=590,ly=236)
 m.flow('Aclarar','Solicitar',[(755,205),(755,165),(320,165),(320,205)])
 m.flow('Referencia','Verificar',[(496,277),(496,375),(575,375),(575,400)],'Sí',lx=520,ly=340)
 m.flow('Verificar','Hay',[(685,450),(735,450)])
 m.flow('Hay','Preparar',[(787,450),(845,450)],'Sí',lx=814,ly=435)
 m.flow('Preparar','Despachar',[(1055,450),(1105,450)])
 m.flow('Despachar','Recibir',[(1300,450),(1315,450),(1315,255),(1330,255)])
 m.flow('Recibir','Conforme',[(1525,255),(1570,255)])
 m.flow('Conforme','Cerrar',[(1596,228),(1596,167),(1600,167)],'Sí',lx=1572,ly=190)
 m.flow('Cerrar','Fin',[(1725,210),(1725,272)])
 m.flow('Conforme','Diferencia',[(1596,280),(1596,400)],'No',lx=1620,ly=341)
 m.flow('Diferencia','FinDiferencia',[(1720,450),(1740,450),(1740,544),(1738,544)])
 m.flow('Hay','Faltante',[(761,476),(761,650)],'No / saldo',lx=810,ly=575)
 m.flow('Faltante','Autorizar',[(870,700),(940,700)])
 m.flow('Autorizar','Compra',[(992,701),(1080,701)],'Sí',lx=1030,ly=685)
 m.flow('Compra','FinCompra',[(1320,701),(1520,701)])
 m.flow('Autorizar','FinNoCompra',[(966,727),(966,745),(989,745),(989,765)],'No',lx=1010,ly=755)
 m.datum('Registro','ID + movimientos + fechas',930,180,215,65,'Despachar',[(1040,245),(1040,330),(1200,330),(1200,400)])
 m.msg('Despachar','Pool_Transporte',[(1200,500),(1200,545),(1340,545),(1340,855),(480,855),(480,885)],'Salida / identificación del traslado',lx=710,ly=846)
 m.msg('Pool_Transporte','Recibir',[(1415,885),(1415,305)],'Entrega / constancia',lx=1510,ly=848)
 m.note(42,1000,1700,'Reglas: compatibilidad incierta → aclarar, sin compra automática. Recepción parcial solo con aceptación y saldo abierto. Diferencias: registrar causa y ajuste autorizado antes de cerrar. Tras recepción de compra, volver a verificar disponibilidad mediante solicitud vinculada.')
 m.note(42,1070,1700,'Fuentes de la brecha: S1 y S2. Diseño: Benjamín, PC3. Línea continua: secuencia; discontinua: mensaje; rombo X: decisión exclusiva; +: subproceso no automático. BPMN 2.0.2 (OMG).')
 m.save()

if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 integral(); international(); internal(); future()
 print('Generados 4 SVG y 3 modelos BPMN con DI en',OUT)
