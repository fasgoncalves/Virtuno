import asyncio

PROXY_PORT = 8022
IP_FILE = '/opt/kvm-manager/current_vm_ip.txt'

async def handle_connection(reader, writer):
    try:
        with open(IP_FILE, 'r') as f:
            dest_ip = f.read().strip()
        print(f'🔁 Redirecionando ligação para {dest_ip}:{PROXY_PORT}')
        
        # Liga ao destino
        remote_reader, remote_writer = await asyncio.open_connection(dest_ip, PROXY_PORT)

        async def forward(src_reader, dst_writer):
            try:
                while not src_reader.at_eof():
                    data = await src_reader.read(4096)
                    if not data:
                        break
                    dst_writer.write(data)
                    await dst_writer.drain()
            except Exception as e:
                print(f"⚠️ Erro ao redirecionar: {e}")
            finally:
                dst_writer.close()

        await asyncio.gather(
            forward(reader, remote_writer),
            forward(remote_reader, writer)
        )
    except Exception as e:
        print(f"❌ Erro: {e}")
        writer.close()

async def main():
    server = await asyncio.start_server(handle_connection, '0.0.0.0', PROXY_PORT)
    print(f"🚀 Proxy ativo na porta {PROXY_PORT} (à escuta para redirecionar)")
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())

