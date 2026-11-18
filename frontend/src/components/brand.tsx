import Image from "next/image";

export function Brand() {
  return (
    <div className="brand">
      <Image src="/fametro.png" alt="Grupo Fametro" width={1484} height={396} unoptimized />
    </div>
  );
}
