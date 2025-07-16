import { useState } from "react";
import Input from "./components/Input";
import Button from "./components/Button";
import Card from "./components/Card";

const initialContacts = [
  { id:1, name:"NZAMBI JEAN DE DIEU", phone:"074816739", whatsapp:"https://wa.me/241074816739", note:"" },
  { id:2, name:"MAKIABA MBAMI, Vianney", phone:"077725946", whatsapp:"https://wa.me/241077725946", note:"" },
  { id:3, name:"BISSELA", phone:"060198364", whatsapp:"https://wa.me/241060198364", note:"" },
  { id:4, name:"orphé MYENE", phone:"077412251", whatsapp:"https://wa.me/241077412251", note:"" },
];

export default function App() {
  const [contacts, setContacts] = useState(initialContacts);
  const [search, setSearch] = useState("");
  const [newContact, setNewContact] = useState({ name:"", phone:"", note:"" });

  const filtered = contacts.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase())
    || c.phone.includes(search)
  );

  const addContact = () => {
    if (!newContact.name||!newContact.phone) return;
    const c = {
      ...newContact,
      id: Date.now(),
      whatsapp: `https://wa.me/241${newContact.phone}`
    };
    setContacts([c, ...contacts]);
    setNewContact({ name:"", phone:"", note:"" });
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Gestion Contacts WhatsApp</h1>
      <Input placeholder="Rechercher nom ou numéro..." value={search} onChange={e=>setSearch(e.target.value)} />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Input placeholder="Nom & Prénoms" value={newContact.name} onChange={e=>setNewContact({...newContact,name:e.target.value})}/>
        <Input placeholder="Téléphone" value={newContact.phone} onChange={e=>setNewContact({...newContact,phone:e.target.value})}/>
        <Input placeholder="Note (optionnel)" value={newContact.note} onChange={e=>setNewContact({...newContact,note:e.target.value})}/>
        <Button onClick={addContact}>Ajouter</Button>
      </div>
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map(c=>(
          <Card key={c.id} title={c.name} subtitle={`Téléphone : ${c.phone}`} note={c.note}>
            <a href={c.whatsapp} target="_blank" className="text-blue-600 underline">Contacter sur WhatsApp</a>
          </Card>
        ))}
      </div>
    </div>
  );
}
