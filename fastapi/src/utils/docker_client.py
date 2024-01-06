import docker
import json
import uuid
from typing import Dict, List, Tuple, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ContainerSchema(BaseModel):
    name: str = Field(..., example="ContainerName", description="Unique name for container.")
    created_at: datetime = Field(..., example="2019-04-01T03:00:00+03:00", description="ISO 8601 format")
    container_id: str = Field(..., example="3b20c82c5981a43aad3c9929c9ef7d0ffe0b22887dd5d448f664d09386eea44b", description="Container id.")
    status: str = Field(..., example="running", description="Container status.")
    running: bool = Field(..., example="True", description="Container running.")
    paused: bool = Field(..., example="False", description="Container paused.")
    restarting: bool = Field(..., example="False", description="Container restarting.")
    log_path: str = Field(..., example="/var/docker/...", description="Log file path.")
    hostname: str = Field(..., example="ovpn_container_995", description="Hostname.")
    ports: List[Tuple[int, int]] = Field(..., example="ovpn_container_995", description="Hostname.")




class DockerClient():
    def __init__(self):
        self.client = docker.from_env()

    def __parse_container_info(self, container_info: dict):
        ports = [(ext_ports[0]["HostPort"],
                  int(int_port.split('/')[0]))
                 for int_port, ext_ports
                 in container_info['NetworkSettings']['Ports'].items()
                 if type(ext_ports) != type(None)]

        container = ContainerSchema(name=container_info['Name'],
                                    created_at=container_info['Created'],
                                    container_id=container_info['Id'],
                                    status=container_info['State']['Status'],
                                    running=container_info['State']['Running'],
                                    paused=container_info['State']['Paused'],
                                    restarting=container_info['State']['Restarting'],
                                    log_path=container_info['LogPath'],
                                    hostname=container_info['Config']['Hostname'],
                                    ports=ports)
        return container.model_dump()

    def container_get(self, container_id: str):
        container = self.client.containers.get(container_id=container_id)
        return self.__parse_container_info(container_info=container.attrs)
        return containers

    def containers_get_list(self):
        containers = [self.__parse_container_info(container_info=container.attrs) for container in self.client.containers.list()]
        return containers

    def container_run(self,
                      image: str,
                      command: str = None,
                      stdout: bool = True,
                      stderr: bool = False,
                      remove: bool = False):
        self.client.containers.run(image=image, command=command, stdout=stdout, stderr=stderr, remove=remove)

    def container_kill(self, container_name: str):
        self.client.api.kill(container=container_name)

    def container_stop(self, container_name: str):
        self.client.api.stop(container=container_name)

    def container_start(self, container_name: str):
        return self.client.api.start(container=container_name)

    def container_exec(self, container_name: str, cmd: str):
        exec_id = self.client.api.exec_create(container=container_name,
                                              cmd=cmd,
                                              stdout=True,
                                              stderr=True,
                                              stdin=True,
                                              tty=True,
                                              privileged=False)['Id']
        byte_result = self.client.api.exec_start(exec_id=exec_id, detach=False, tty=True, demux=False)
        return byte_result.decode("utf-8")


    def container_create(self,
                         name: str,
                         image: str,
                         hostname: str,
                         working_dir: str = None,
                         command: str = None,
                         entrypoint: str = None,
                         environment: Dict[str, int or str] = None,
                         volumes: List[str] = None,
                         ports: List[int] = None,
                         detach: bool = False,
                         tty: bool = False) -> str:
        container = self.client.api.create_container(name=name,
                                                     image=image,
                                                     hostname=hostname,
                                                     working_dir=working_dir,
                                                     command=command,
                                                     entrypoint=entrypoint,
                                                     environment=environment,
                                                     volumes=volumes,
                                                     ports=ports,
                                                     detach=detach,
                                                     tty=tty)
        return container['Id']


class OVPN_Docker_Client(DockerClient):
    def __init__(self):
        DockerClient.__init__(self)

    def remove_ovpn_server_container(self, name: str):
        self.container_kill(container_name=name)
        self.client.api.remove_container(container=name, force=True)


    def create_ovpn_server_container(self,
                                     name: str,
                                     ports: List[Tuple[int, int]] = [(1194, 1194),],
                                     run_after_creation: bool = True):
        image = 'deaffella/ovpn:server-1.0'
        working_dir = '/ovpn'
        #command = '/ovpn'
        container_id = self.container_create(name=name,
                                             image=image,
                                             hostname=name,
                                             working_dir=working_dir,
                                             entrypoint='bash',
                                             environment={'TZ': 'Europe/Moscow'},
                                             ports=ports,
                                             detach=True,
                                             tty=True)
        if run_after_creation:
            self.container_start(container_name=container_id)
            container_status = self.container_get(container_id=container_id)['status']
            print()
            print(container_status)
            print()

    def configure_ovpn_server_container(self, name: str, ext_ip: str, subnet: str = '192.168.42.0', mask: int = 24):
        cmd = f'bash configure_server.sh --ext_ip {ext_ip} --subnet {subnet} --mask {mask}'
        exec_result = self.container_exec(container_name=name, cmd=cmd)
        print(exec_result)

    def ovpn_certificate_create(self,
                                container_name: str,
                                cert_name: str,
                                ip: str):
        self.container_exec(container_name=container_name,
                            cmd=f'easyrsa build-client-full {cert_name} nopass')
        self.container_exec(container_name=container_name,
                            cmd=f'bash -c "echo ' + f"'ifconfig-push {ip} 255.255.255.0'" + f' > /etc/openvpn/ccd/{cert_name}"')
        self.container_exec(container_name=container_name,
                            cmd=f'bash -c "ovpn_getclient {cert_name} > ./clients/{cert_name}.ovpn"')

    def ovpn_certificate_remove(self, container_name: str, cert_name: str):
        self.container_exec(container_name=container_name,
                            cmd=f'cp -f "$EASYRSA_PKI/crl.pem" "$OPENVPN/crl.pem"')
        self.container_exec(container_name=container_name,
                            cmd=f'chmod 644 "$OPENVPN/crl.pem"')
        self.container_exec(container_name=container_name,
                            cmd=f'rm /etc/openvpn/ccd/{cert_name}')
        self.container_exec(container_name=container_name,
                            cmd=f'rm /etc/openvpn/ccd/{cert_name}.ovpn')
        self.container_exec(container_name=container_name,
                            cmd=f'rm ./clients/{cert_name}.ovpn')




if __name__=='__main__':
    client = OVPN_Docker_Client()

    # client.containers_get()
    # print(client.containers_get())

    # ext_ip = 'curl -s http://whatismijnip.nl |cut -d " " -f 5'
    ext_ip = '188.243.151.68'
    subnet = '192.168.51.0'
    name = 'ovpn_server'

    # client.create_ovpn_server_container(name=name)
    # client.configure_ovpn_server_container(name=name, ext_ip=ext_ip, subnet=subnet)
    # client.ovpn_certificate_create(container_name=name, cert_name='5', ip='192.168.51.20')
    # client.ovpn_certificate_remove(container_name=name, cert_name='5')

    client.remove_ovpn_server_container(name=name)



