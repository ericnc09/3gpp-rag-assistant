# Human calibration — context for each answer

Score each answer in `human_calibration.csv` on the judge's rubric (scripts/eval/judge.py), using only the context below:

- **faithfulness 0-5**: 5 = every claim traces to the context; 3 = one unsupported claim; 1 = several; 0 = ignores the context.
- **correctness 0-5**: 5 = accurate and complete given the context; 3 = partial; 1 = mostly wrong; 0 = does not address the question.

The judge's scores are deliberately not shown. Score blind.

## gs-001: What is gNB?

### Answer

According to the provided context, a gNB (gNB Central Unit) is a logical node hosting RRC, SDAP and PDCP protocols of the gNB or RRC and PDCP protocols of the en-gNB that controls the operation of one or more gNB-DUs [D1].

### Context

**[D1] 38401.docx**

F1-terminating IAB-donor: Refers to the IAB-donor that terminates F1 for the boundary IAB-node or a mobile IAB-node. First U2N Relay UE: as defined in TS 38.300 [2]. gNB: as defined in TS 38.300 [2]. gNB Central Unit (gNB-CU): a logical node hosting RRC, SDAP and PDCP protocols of the gNB or RRC and PDCP protocols of the en-gNB that controls the operation of one or more gNB-DUs. The gNB-CU terminates the F1 interface connected with the gNB-DU. gNB Distributed Unit (gNB-DU): a logical node hosting RLC, MAC and PHY layers of the gNB or en-gNB, and its operation is partly controlled by gNB-CU. One gNB-DU supports one or multiple cells. One cell is supported by only one gNB-DU. The gNB-DU terminates the F1 interface connected with the gNB-CU. For DC operation, the MgNB-DU designates the gNB-DU of an en-gNB or a gNB acting as master node, and the SgNB-DU designates the gNB-DU of an en-gNB or a gNB acting as secondary node. gNB-CU-Control Plane (gNB-CU-CP): a logical node hosting the RRC and the control plane part of the PDCP protocol of the gNB-CU for an en-gNB or a gNB.

**[D2] 38300.docx**

on: an identifier used during SNPN selection to enhance the likelihood of selecting a preferred SNPN that supports a Default Credentials Server or a Credentials Holder, as specified in TS 23.501 [3]. gNB: node providing NR user plane and control plane protocol terminations towards the UE, and connected via the NG interface to the 5GC. gNB-reader: an A-IoT reader that is deployed within the gNB, as defined in 16.23. High Altitude Platform Station: airborne vehicle embarking the NTN payload placed at an altitude between 8 and 50 km. IAB-donor: gNB that provides network access to UEs via a network of backhaul and access links. IAB-donor-CU: as defined in TS 38.401 [4]. IAB-donor-DU: as defined in TS 38.401 [4]. IAB-DU: gNB-DU functionality supported by the IAB-node to terminate the NR access interface to UEs and next-hop IAB-nodes, and to terminate the F1 protocol to the gNB-CU functionality, as defined in TS 38.401 [4], on the IAB-donor.

**[D3] 38401.docx**

of an en-gNB or a gNB acting as secondary node. gNB-CU-Control Plane (gNB-CU-CP): a logical node hosting the RRC and the control plane part of the PDCP protocol of the gNB-CU for an en-gNB or a gNB. The gNB-CU-CP terminates the E1 interface connected with the gNB-CU-UP and the F1-C interface connected with the gNB-DU. For DC operation, the MgNB-CU-CP designates the gNB-CU-CP of the gNB-CU for an en-gNB or a gNB acting as master node, and the SgNB-CU-CP designates the gNB-CU-CP of the gNB-CU for an en-gNB or a gNB acting as secondary node. gNB-CU-User Plane (gNB-CU-UP): a logical node hosting the user plane part of the PDCP protocol of the gNB-CU for an en-gNB, and the user plane part of the PDCP protocol and the SDAP protocol of the gNB-CU for a gNB. The gNB-CU-UP terminates the E1 interface connected with the gNB-CU-CP and the F1-U interface connected with the gNB-DU. For DC operation, the MgNB-CU-UP designates the gNB-CU-UP of the gNB-CU for an en-gNB or a gNB acting as master node,

**[D4] 23501.docx**

usly one 3GPP access network and one non-3GPP access network. MINT-EPS: As defined in TS 23.122 [17]. Mobile Base Station Relay: A mobile base station acts as a relay between a UE and the 5G network. Such mobile base station relay can for example be mounted on a moving vehicle and serve UEs that can be located inside or outside the vehicle (or entering/leaving the vehicle). See description of TS 22.261 [2]. A mobile Base Station Relay is supported in 5GS with the IAB-architecture with mobility as specified in clause 5.35A and that described in TS 38.401 [42]. Mobile gNB with Wireless Access Backhauling (MWAB): A NG-RAN device comprised of a UE (MWAB-UE) and a gNB (MWAB-gNB). The MWAB provides an NR access link to UEs and connects wirelessly to the 5GC (using NR) of a PLMN or SNPN broadcasted by its cell(s), through an IP/Ethernet connectivity provided by a Backhaul (BH) PDU sessions established by the MWAB-UE via the NG-RAN of a Backhaul(BH) PLMN/SNPN. Such device may be mobile, e.g.

**[D5] 38473.docx**

esponse to the GNB-DU RESOURCE COORDINATION REQUEST. Direction: gNB-DU gNB-CU ## 9.2.1.15 GNB-DU STATUS INDICATION This message is sent by the gNB-DU to indicate to the gNB-CU its status of overload. Direction: gNB-DU gNB-CU ## 9.2.1.16 F1 REMOVAL REQUEST This message is sent by either the gNB-DU or the gNB-CU to intiate the removal of the interface instance and the related resources. Direction: gNB-DU gNB-CU, gNB-CU gNB-DU. ## 9.2.1.17 F1 REMOVAL RESPONSE This message is sent by either the gNB-DU or the gNB-CU to acknowledge the initiation of removal of the interface instance and the related resources. Direction: gNB-CU gNB-DU, gNB-DU gNB-CU. ## 9.2.1.18 F1 REMOVAL FAILURE This message is sent by either the gNB-DU or the gNB-CU to indicate that removing the interface instance and the related resources cannot be accepted. Direction: gNB-CU gNB-DU, gNB-DU gNB-CU. ## 9.2.1.19 NETWORK ACCESS RATE REDUCTION This message is sent by the gNB-CU to indicate to the gNB-DU a need to reduce the rate at which UEs access the network.

## gs-003: What is the E1 interface used for in 5G NG-RAN?

### Answer

The E1 interface is used for the connection between ng-eNB-CU and ng-eNB-DU in the 5G NG-RAN architecture, as specified in clause 8.1 of TS 38.401 [D4].

### Context

**[D1] 38413.docx**

shall, if supported, update the 5G ProSe authorization information for the UE accordingly. If the 5G ProSe Authorized IE includes one or more IEs set to not authorized, the NG-RAN node shall, if supported, initiate actions to ensure that the UE is no longer accessing the relevant 5G ProSe service(s). If the 5G ProSe UE PC5 Aggregate Maximum Bit Rate IE is included in the UE CONTEXT MODIFICATION REQUEST message, the NG-RAN node shall, if supported: - replace the previously provided 5G ProSe UE PC5 Aggregate Maximum Bit Rate, if available in the UE context, with the received value; - use the received value for the concerned UEs sidelink communication in network scheduled mode for 5G ProSe services. If the 5G ProSe PC5 QoS Parameters IE is included in the UE CONTEXT MODIFICATION REQUEST message, the NG-RAN node shall, if supported, use it as defined in TS 23.304 [47]. If the Network Controlled Repeater Authorized IE is included in the UE CONTEXT MODIFICATION REQUEST message, the NG-RAN no

**[D2] 38401.docx**

also apply to ng-eNB and W1/E1 interface, i.e. W1 interface between ng-eNB-DU and ng-eNB-CU-CP/ng-eNB-CU-UP, E1 interface between ng-eNB-CU-CP and ng-eNB-CU-UP, if not explicitly specified otherwise. ## 8.9.1 UE Initial Access The signalling flow for UE Initial access involving E1 and F1 is shown in Figure 8.9.1-1. Figure 8.9.1-1: UE Initial Access procedure involving E1 and F1 Steps 1-8 are defined in clause 8.1. 9. The gNB-CU-CP sends the BEARER CONTEXT SETUP REQUEST message to establish the bearer context in the gNB-CU-UP. 10 The gNB-CU-UP sends the BEARER CONTEXT SETUP RESPONSE message to the gNB-CU-CP, including F1-U UL TEID and transport layer address allocated by the gNB-CU-UP. Steps 11-13 are defined in clause 8.1. 14. The gNB-CU-CP sends the BEARER CONTEXT MODIFICATION REQUEST message to the gNB-CU-UP, including F1-U DL TEID and transport layer address allocated by the gNB-DU. 15. The gNB-CU-UP sends the BEARER CONTEXT MODIFICATION RESPONSE message to the gNB-CU-CP. Steps 16-22 are defined in clause 8.1.

**[D3] 38401.docx**

zed TDD-unicast areas in order to achieve interoperability in coexistence scenarios. ## 10 NG-RAN interfaces ## 10.1 NG interface TS 38.410 [14] specifies NG interface general aspects and principles. ## 10.2 Xn interface TS 38.420 [15] specifies Xn interface general aspects and principles. ## 10.3 F1 interface TS 38.470 [16] specifies F1 interface general aspects and principles. ## 10.4 E1 interface TS 37.480 [17] specifies E1 interface general aspects and principles. ## 10.5 Antenna interface - general principles TS 37.460 [35] specifies Iuant interface general aspects and principles. The Iuant interface for the control of RET antennas or TMAs is a logical part of the NG-RAN. The support of any standardised antenna interface technique shall not be prevented; e.g. AISG (Antenna interface standards group) specifications may be used. ## 11 Overall procedures in NG-RAN Architecure ## 11.1 Multiple TNLAs for Xn-C In the following, the procedure for managing multiple TNLAs for Xn-C is described. Figure 11.1-1: Managing multiple TNLAs for Xn-C. 1.

**[D4] 38401.docx**

nnected to the 5GC through the NG interface. NOTE 1: As specified in TS 38.300 [2], NG-RAN could also consists of a set of ng-eNBs, an ng-eNB may consist of an ng-eNB-CU and one or more ng-eNB-DU(s). An ng-eNB-CU and an ng-eNB-DU is connected via W1 interface. The general principle described in this clause also applies to ng-eNB and W1 interface, if not explicitly specified otherwise. An gNB can support FDD mode, TDD mode or dual mode operation. gNBs can be interconnected through the Xn interface. A gNB may consist of a gNB-CU and one or more gNB-DU(s). A gNB-CU and a gNB-DU is connected via F1 interface. One gNB-DU is connected to only one gNB-CU. NOTE 2: In case of network sharing with multiple cell ID broadcast, each Cell Identity associated with a subset of PLMNs, PNI-NPNs or SNPNs corresponds to a gNB-DU and the gNB-CU it is connected to, i.e. the corresponding gNB-DUs share the same physical layer cell resources. NOTE 3: For resiliency, a gNB-DU may be connected to multiple gNB-CUs by appropriate implementation. NG, Xn and F1 are logical interfaces.

**[D5] 38413.docx**

at MBS session within the Data Forwarding Response MRB List IE in the MBS Active Session Information Target to Source List IE in the Target NG-RAN Node to Source NG-RAN Node Transparent Container IE. If the Time Synchronisation Assistance Information IE is included in the HANDOVER REQUEST message, the NG-RAN node shall, if supported, store the information in the UE context and use it as defined in TS 23.501 [9]. If the 5G ProSe Authorized IE is contained in the HANDOVER REQUEST message and it contains one or more IEs set to authorized, the NG-RAN node shall, if supported, consider that the UE is authorized for the relevant service(s). If the 5G ProSe UE PC5 Aggregate Maximum Bit Rate IE is included in the HANDOVER REQUEST message, the NG-RAN node shall, if supported, use the received value for the concerned UEs sidelink communication in network scheduled mode for 5G ProSe services. If the 5G ProSe PC5 QoS Parameters IE is included in the HANDOVER REQUEST message, the NG-RAN node shall, if supported, use it as defined in TS 23.304 [47].

## gs-004: What are the NG-RAN logical nodes and their functions?

### Answer

The NG-RAN logical nodes and their functions are defined as part of the RNL (Radio Network Layer) of the NG-RAN architecture, which consists of a set of gNBs (gNBs) and ng-eNBs (ng-eNBs) connected to the 5GC through the NG interface, as specified in TS 38.300 [7].

The specific functions of the NG-RAN logical nodes are not explicitly stated in the provided context excerpts. However, the functions of the NG-RAN are described in other clauses of TS 38.401, such as clause 7, which lists the NG-RAN functions description, including NG-RAN sharing, Remote Interference Management, Cross-Link Interference Management, Support for Non-Public Networks, RACH Optimisation Function, Positioning, Support for NR MBS, and PCI Optimisation Function, among others.

Therefore, the NG-RAN logical nodes and their functions are not explicitly stated in the provided context excerpts, but can be inferred from other clauses of TS 38.401.

### Context

**[D1] 38401.docx**

Node 30 6.6 A-IoT related contexts in an NG-RAN Node 31 7 NG-RAN functions description 31 7.0 General 31 7.1 NG-RAN sharing 31 7.2 Remote Interference Management 31 7.3 Cross-Link Interference Management 32 7.4 Support for Non-Public Networks 32 7.5 RACH Optimisation Function 32 7.6 Positioning 32 7.7 Support for NR MBS 32 7.7.1 Support of dynamic PTP and PTM switching 33 7.7.2 Support of resource efficiency for RAN Sharing 33 7.7.2.1 General 33 7.7.2.2 Support of resource efficiency for MOCN 33 7.7.2.3 Support of resource efficiency for RAN Sharing with multiple cell-ID broadcast 33 7.7.3 Support of Multicast reception for UEs in RRC_INACTIVE 33 7.7.4 Recovery of shared F1-U Failure 34 7.8 PCI Optimisation Function 34 7.9 Support for CCO 34 7.9.1 General 34 7.9.2 OAM requirements 34 7.9.3 Dynamic coverage configuration changes 35 7.10 Support of RAN visible QoE measurement 35 7.11 Support of AI/ML for NG-RAN 35 7.11.1 General 35 7.11.2 OAM requirements 35 7.11.3 Data Collection and R

**[D2] 38401.docx**

chitecture as well as the NG-RAN interfaces are the following: - Logical separation of signalling and data transport networks. - NG-RAN and 5GC functions are fully separated from transport functions. Addressing scheme used in NG-RAN and 5GC shall not be tied to the addressing schemes of transport functions. The fact that some NG-RAN or 5GC functions reside in the same equipment as some transport functions does not make the transport functions part of the NG-RAN or the 5GC. - Mobility for an RRC connection is fully controlled by the NG-RAN. - The NG-RAN interfaces are defined along the following principles: - The functional division across the interfaces have as few options as possible. - Interfaces are based on a logical model of the entity controlled through this interface. - One physical network element can implement multiple logical nodes. ## 5 General architecture ## 5.1 General The protocols over Uu and NG interfaces are divided into two structures: - User plane protocols These are the protocols implementing the actual PDU Session service, i.e.

**[D3] 38420.docx**

the Xn is a point-to-point interface between two NG-RAN nodes. A point-to-point logical interface should be feasible even in the absence of a physical direct connection between the two NG-RAN nodes. ## 4.3 Xn interface specification objectives The Xn interface specifications facilitate the following: - inter-connection of NG-RAN nodes supplied by different manufacturers; - support of continuation between NG-RAN nodes of the NG-RAN services offered via the NG interface; - separation of Xn interface Radio Network functionality and Transport Network functionality to facilitate introduction of future technology. ## 4.4 Xn interface capabilities The Xn interface supports: - procedures to support intra-NG-RAN mobility; - procedures to support dual connectivity between NG-RAN nodes. ## 5 Functions of the Xn interface ## 5.1 General The following clauses describe the functions supported in Xn interface.

**[D4] 38410.docx**

t of Things LP-WUS Low Power Wake Up Signal MBS Multicast/Broadcast Service MT Mobile Terminated NB-IoT Narrow Band Internet of Things NG-U NG User plane interface PEI Paging Early Indication PTP Point to Point PTM Point to Multipoint QMC QoE Measurement Collection QoE Quality of Experience RAT Radio Access Technology RIM Remote Interference Management RNL Radio Network Layer SMF Session Management Function UP User Plane UPF User Plane Function ## 4 General aspects ## 4.1 NG Architecture The NG-RAN is layered into a Radio Network Layer (RNL) and a Transport Network Layer (TNL). The NG-RAN architecture, i.e. the NG-RAN logical nodes and interfaces between them, are defined as part of the RNL. The NG-RAN architecture consists of a set of gNBs and ng-eNBs which are connected to the 5GC through the NG interface and is specified in TS 38.300 [7]. The NG-RAN may have several NG access points towards the 5GC. As a minimum, each NG access point (in NG-RAN or 5GC) shall independently fulfil the requirements of the relevant NG specifications (3GPP 38.41x series - see clause 7).

**[D5] 38410.docx**

access points towards the 5GC. As a minimum, each NG access point (in NG-RAN or 5GC) shall independently fulfil the requirements of the relevant NG specifications (3GPP 38.41x series - see clause 7). NG is a logical interface. There may be multiple NG-C logical interfaces towards the 5GC from any one NG-RAN node. The selection of the NG-C interface is then determined by the NAS Node Selection function as described in clause 5. There may be multiple NG-U logical interfaces towards the 5GC from any one NG-RAN node. The selection of the NG-U interface is done within the 5GC and signalled to the NG-RAN node by the AMF. ## 4.2 NG interface general principles The general principles for the specification of the NG interface are as follows: - the NG interface is open; - the NG interface supports the exchange of signalling information between the NG-RAN and 5GC; - from a logical standpoint, the NG is a point-to-point interface between an NG-RAN node and a 5GC node.

## gs-006: What is the Xn interface between gNBs used for?

### Answer

The Xn interface between gNBs is used to interconnect gNBs with each other, as well as to provide a point-to-point logical interface between two NG-RAN nodes, even in the absence of a physical direct connection between them [D1, D2].

This interface supports the exchange of signalling information between two NG-RAN nodes, and the forwarding of PDUs to the respective tunnel endpoints [D2]. 

The Xn interface is open, and it supports the exchange of signalling information between two NG-RAN nodes, and the forwarding of PDUs to the respective tunnel endpoints [D2].

The Xn interface is used for procedures to support dual connectivity between NG-RAN nodes [D2]. 

The Xn interface is used for procedures to support intra-NG-RAN mobility [D2]. 

The Xn interface is used for separation of Xn interface Radio Network functionality and Transport Network functionality to facilitate introduction of future technology [D1]. 

The Xn interface is used for inter-connection of NG-RAN nodes supplied by different manufacturers [D1]. 

The Xn interface is used for support of continuation between NG-RAN nodes of the NG interface [D1].

### Context

**[D1] 38420.docx**

the Xn is a point-to-point interface between two NG-RAN nodes. A point-to-point logical interface should be feasible even in the absence of a physical direct connection between the two NG-RAN nodes. ## 4.3 Xn interface specification objectives The Xn interface specifications facilitate the following: - inter-connection of NG-RAN nodes supplied by different manufacturers; - support of continuation between NG-RAN nodes of the NG-RAN services offered via the NG interface; - separation of Xn interface Radio Network functionality and Transport Network functionality to facilitate introduction of future technology. ## 4.4 Xn interface capabilities The Xn interface supports: - procedures to support intra-NG-RAN mobility; - procedures to support dual connectivity between NG-RAN nodes. ## 5 Functions of the Xn interface ## 5.1 General The following clauses describe the functions supported in Xn interface.

**[D2] 38420.docx**

if any, in 3GPP TR 21.905 [1]. CLI Cross Link Interference IAB Integrated Access and Backhaul LP-WUS Low Power Wake Up Signal LTM L1/L2 Triggered Mobility MBS Multicast Broadcast Service QMC QoE Measurement Collection QoE Quality of Experience SCTP Stream Control Transmission Protocol Xn-C Xn Control plane Xn-U Xn User plane ## 4 General aspects ## 4.1 Introduction The interface allowing to interconnect NG-RAN nodes with each other is referred to as the Xn interface. ## 4.2 Xn interface general principles The general principles for the specification of the Xn interface are as follows: - the Xn interface is open; - the Xn interface supports the exchange of signalling information between two NG-RAN nodes, and the forwarding of PDUs to the respective tunnel endpoints; - from a logical standpoint, the Xn is a point-to-point interface between two NG-RAN nodes. A point-to-point logical interface should be feasible even in the absence of a physical direct connection between the two NG-RAN nodes.

**[D3] 38401.docx**

onding gNB-DUs share the same physical layer cell resources. NOTE 3: For resiliency, a gNB-DU may be connected to multiple gNB-CUs by appropriate implementation. NG, Xn and F1 are logical interfaces. For NG-RAN, the NG and Xn-C interfaces for a gNB consisting of a gNB-CU and gNB-DUs, terminate in the gNB-CU. For EN-DC, the S1-U and X2-C interfaces for a gNB consisting of a gNB-CU and gNB-DUs, terminate in the gNB-CU. The gNB-CU and connected gNB-DUs are only visible to other gNBs and the 5GC as a gNB. A possible deployment scenario is described in Annex A. The node hosting user plane part of NR PDCP (e.g. gNB-CU, gNB-CU-UP, and for EN-DC, MeNB or SgNB depending on the bearer split) may perform user inactivity monitoring and further inform its inactivity or (re)activation to the node having C-plane connection towards the core network (e.g. over E1, X2, Xn). The node hosting NR RLC (e.g. gNB-DU) may perform user inactivity monitoring and further inform its inactivity or (re)activation to the node hosting control plane, e.g. gNB-CU or gNB-CU-CP. UL PDCP configuration (i.e.

**[D4] 38300.docx**

is either: - a gNB, providing NR user plane and control plane protocol terminations towards the UE; or - an ng-eNB, providing E-UTRA user plane and control plane protocol terminations towards the UE. The gNBs and ng-eNBs are interconnected with each other by means of the Xn interface. The gNBs and ng-eNBs are also connected by means of the NG interfaces to the 5GC, more specifically to the AMF (Access and Mobility Management Function) by means of the NG-C interface and to the UPF (User Plane Function) by means of the NG-U interface (see TS 23.501 [3]). NOTE: The architecture and the F1 interface for a functional split are defined in TS 38.401 [4]. The NG-RAN architecture is illustrated in Figure 4.1-1 below. Figure 4.1-1: Overall Architecture ## 4.2 Functional Split The gNB and ng-eNB host the following functions: - Functions for Radio Resource Management: Radio Bearer Control, Radio Admission Control, Connection Mobility Control, Dynamic allocation of resources to UEs in uplink, downl

**[D5] 38401.docx**

sec tunnel mode to protect the OAM, NG and/or Xn traffic, the IP address(es) of the WAB-MT is used as outer IP address(es). The allocation of the inner tunnel IP address(es) is outside of 3GPP scope. ## 12.2.3 TAC and RANAC (re-)configurations for a WAB-gNBs cell The TAC and RANAC of WAB-gNBs cell are configured by the OAM. During the mobility of WAB-node, they can be reconfigured by the OAM, or they can remain unchanged in a certain geographical area. The TAC and RANAC of the WAB-gNBs cell may be the same as, or different than, the TAC and RANAC of the co-located WAB-MTs serving cell, respectively. The TAC and RANAC of the WAB-gNBs cell can be changed in order to reflect the WAB-nodes physical location. ## 12.3 NG connection management Based on the OAM configuration, the WAB-gNB can set up NG interface with an AMF. When disconnecting from an AMF is required, due to inter-AMF mobility of a WAB-gNB, or when the authorization status of the WAB-gNB changes from authorized to not authorize

## gs-007: What is the difference between SA and NSA 5G deployment options?

### Answer

The difference between SA (Standalone) and NSA (Non-Standalone) 5G deployment options is primarily related to the network architecture and the way the user equipment (UE) interacts with the network.

In an NSA deployment, the UE uses the same radio access technology (RAT) as the previous generation (4G) network, and the 5G network is built on top of the 4G network using a non-standalone architecture. This means that the UE can seamlessly switch between the 4G and 5G networks, and the 5G network does not require a separate connection to the 5G core network.

In contrast, an SA deployment uses a standalone 5G architecture, where the UE connects directly to the 5G core network, and the 5G network is not built on top of the 4G network. This means that the UE must be capable of supporting the 5G RAT, and the 5G network requires a separate connection to the 5G core network.

The key difference between SA and NSA deployment options is the level of network separation and the way the UE interacts with the network. SA deployment provides a more secure and isolated environment, while NSA deployment provides a more seamless and backward-compatible experience.

[TS 22.261, TS 23.501], [TS 23.502]

### Context

**[D1] 23501.docx**

oncatenated for all of the grid points to produce the satellite coverage availability information. When SMS is used to deliver the satellite coverage availability information, the UE input and satellite coverage availability information output can be delivered in a series of concatenated SMS messages using possibly the same format. ## Annex R (Informative): 5GS support for Indirect Network Sharing deployment ## R.1 General This annex provides guidance on how 5GS features and capabilities can be used to support Indirect Network Sharing deployment option which is specified in clause 6.21 of TS 22.261 [2]. The Indirect Network Sharing deployment option is described in clause 5.18 and further illustrated in the Figure 5.18.1-2. In the geographical areas with Indirect Network Sharing deployment, the existing mobility restriction mechanisms specified in clause 5.3.4.1 can be applied. This can be controlled by the UE subscription data related to mobility restriction and Indirect Network Sharing policies in the serving AMF. For the mobility management, the related procedures (e.g.

**[D2] 36331.docx**

n v2x-InterFreqInfoList of SIB21 is N, the value N1 corresponds to the frequency of the first entry which is included in v2x-InterFreqInfoList broadcast in SIB26 and has a frequency not included in SIB21, the value N2 corresponds to the frequency of the second entry which is included in v2x-InterFreqInfoList broadcast in SIB26 and has a frequency not included in SIB21, and so on. The value 0 corresponds the PCells frequency. v2x-DestinationInfoList Indicates the destination(s) for V2X sidelink communication. v2x-TypeTxSync Indicates the synchronization reference used by the UE. SystemInformationBlockType1 field descriptions bandwithReducedAccessRelatedInfo Access related information for BL UEs and UEs in CE. NOTE 3. campingAllowedInCE Indicates whether non-BL UE is allowed to camp in the non-standalone BL cell in enhanced coverage mode when S-criterion for normal coverage is fulfilled. The field is not applicable for standalone BL cell. category0Allowed The presence of this field indicates category 0 UEs are allowed to access the cell.

**[D3] 23502.docx**

UE communication for 5G VN services 945 M.1 General 945 M.2 Procedures 945 M.2.1 Establishment of communication 945 M.2.2 Change of routing paths due to change of satellites 945 M.2.2.1 General 945 M.2.2.2 Continuation of optimized user packet routing 945 M.2.2.3 Ground fallback with ULCL and recovery of optimized user packet routing 947 M.2.2.3.1 Ground fallback with ULCL 947 M.2.2.3.2 Recovery of optimized user packet routing 948 M.2.2.4 Ground fallback without ULCL 949 Annex M (informative): Change history 953 ## Foreword This Technical Specification has been produced by the 3rd Generation Partnership Project (3GPP). The contents of the present document are subject to continuing work within the TSG and may change following formal TSG approval. Should the TSG modify the contents of the present document, it will be re-released by the TSG with an identifying change of release date and an increase in version number as follows: Version x.y.z where: x the first digit: 1 presented to TSG f

**[D4] 38401.docx**

DU Mobile IAB Distributed Unit mIAB-MT Mobile IAB Mobile Termination MP Multi-Path MRB MBS Radio Bearer MRDC Multi-Radio Dual Connectivity ML Machine Learning MT-SDT Mobile Terminated Small Data Transmission N3C Non-3GPP Connection NAS Non-Access Stratum NES Network Energy Savings NCI NR Cell Identity NDS Network Domain Security NID Network identifier NPN Non-Public Network NSA Non Standalone OAM Operation, Administration and Maintenance OD-SIB1 On-demand SIB1 PLMN Public Land Mobile Network PNI-NPN Public Network Integrated Non-Public Network PTP Point to Point PTM Point to Multipoint PWS Public Warning System QoE Quality of Experience QoS Quality of Service RANAC RAN Area Code RET Remote Electrical Tilting RIM Remote Interference Management RIM-RS Remote Interference Management Reference Signal RLF Radio Link Failure RNL Radio Network Layer RRC Radio Resource Control SA Standalone SAP Service Access Point SCG Secondary Cell Group SCTP Stream Control Transmission Protocol SDT Small Da

**[D5] 38211.docx**

s to NR support for dedicated spectrum less than 5MHz for FR1 | 18.1.0 2023-12 | RAN#102 | RP-233705 | 0117 | - | F | Corrections to MIMO enhancements | 18.1.0 2023-12 | RAN#102 | RP-233718 | 0118 | - | F | Corrections to NR Network-controlled Repeaters | 18.1.0 2023-12 | RAN#102 | RP-233719 | 0119 | - | F | Corrections to positioning enhancements | 18.1.0 2023-12 | RAN#102 | RP-233733 | 0120 | - | B | Introduction of multicast reception in RRC_INACTIVE | 18.1.0 2024-03 | RAN#103 | RP-240518 | 0122 | - | F | Corrections to MIMO enhancements | 18.2.0 2024-03 | RAN#103 | RP-240528 | 0123 | - | F | Corrections to positioning enhancements | 18.2.0 2024-03 | RAN#103 | RP-240535 | 0125 | - | A | Alignment of parameter names | 18.2.0 2024-03 | RAN#103 | RP-240519 | 0126 | - | F | Corrections to sidelink enhancements | 18.2.0 2024-06 | RAN#104 | RP-241061 | 0127 | - | F | Correction for hop counting in SRS for positioning with tx hopping | 18.3.0 2024-06 | RAN#104 | RP-241075 | 0128 | - | F |

## gs-008: What is the NR MAC protocol and what are its main functions?

### Answer

The NR MAC protocol is specified in 3GPP TS 38.321 [D3]. 

The main functions of the NR MAC protocol include: 

- Medium Access Control (MAC) protocol specification [D3]; 
- Mapping between a QoS flow and a data radio bearer [D3]; 
- Transfer of data (user plane or control plane); 
- Header compression and decompression using the ROHC protocol; 
- Header compression and decompression using EHC protocol; 
- Compression and decompression of uplink PDCP SDUs: DEFLATE based UDC only; 
- Ciphering and deciphering; 
- Integrity protection and integrity verification; 
- Timer based SDU discard; 
- For split bearers, routing; 
- Duplication; 
- Reordering and in-order delivery; 
- Out-of-order delivery; 
- Duplicate discarding [D3].

### Context

**[D1] 36300.docx**

C (terminated in ng-eNB on the network side) performs the functions listed in clause 7; - NAS control protocol (terminated in AMF on the network side) performs the functions listed in TS 24.501 [91]. NOTE: For a NB-IoT UE that only supports Control Plane CIoT 5GS Optimisation, as defined in TS 24.501 [91], PDCP is bypassed. For a NB-IoT UE that supports Control Plane CIoT 5GS Optimisation and NG-U data transfer or User Plane CIoT 5GS Optimisation, as defined in TS 24.501 [91], PDCP is not used until AS security is activated. ## 24.3 Layer 2 Except for NB-IoT, the layer 2 of E-UTRA connected to 5GC is split into the following sublayers: Medium Access Control (MAC), Radio Link Control (RLC), NR Packet Data Convergence Protocol (PDCP) and Service Data Adaptation Protocol (SDAP). - The physical layer offers to the MAC sublayer transport channels, see clause 5; - The MAC sublayer offers to the RLC sublayer logical channels, see clause 6.1; - The RLC sublayer offers to the NR PDCP sublayer R

**[D2] 38423.docx**

38.304: NR; User Equipment (UE) procedures in Idle mode and RRC Inactive state. [34] 3GPP TS 36.304: Evolved Universal Terrestrial Radio Access (E-UTRA); User Equipment (UE) procedures in idle mode. [35] 3GPP TS 38.321: NR; Medium Access Control (MAC) protocol specification. [36] 3GPP TS 36.321: Evolved Universal Terrestrial Radio Access (E-UTRA); Medium Access Control (MAC) protocol specification. [37] IETF RFC 5905: Network Time Protocol Version 4: Protocol and Algorithms Specification. [38] 3GPP TS 23.287: Architecture enhancements for 5G System (5GS) to support Vehicle-to-Everything (V2X) services. [39] 3GPP TS 38.211: NR; Physical channels and modulation. [40] 3GPP TS 38.213: NR; Physical layer procedures for control. [41] 3GPP TS 38.473: NG-RAN; F1 application protocol (F1AP). [42] 3GPP TS 38.314: NR; Layer 2 measurements. [43] 3GPP TS 37.320:  Radio measurement collection for Minimization of Drive Tests (MDT), [44] 3GPP TS 36.423:  Evolved Universal Terrestrial Radio Access Network (E-UTRAN); X2 application protocol (X2AP).

**[D3] 38321.docx**

pe The present document specifies the NR MAC protocol. ## 2 References The following documents contain provisions which, through reference in this text, constitute provisions of the present document. - References are either specific (identified by date of publication, edition number, version number, etc.) or non-specific. - For a specific reference, subsequent revisions do not apply. - For a non-specific reference, the latest version applies. In the case of a reference to a 3GPP document (including a GSM document), a non-specific reference implicitly refers to the latest version of that document in the same Release as the present document. [1] 3GPP TR 21.905: Vocabulary for 3GPP Specifications. [2] 3GPP TS 38.300: NR; Overall description; Stage 2. [3] 3GPP TS 38.322: NR; Radio Link Control (RLC) protocol specification. [4] 3GPP TS 38.323: NR; Packet Data Convergence Protocol (PDCP) protocol specification. [5] 3GPP TS 38.331: NR; Radio Resource Control (RRC); Protocol specification. [6] 3GPP TS 38.213: NR; Physical Layer Procedures for control.

**[D4] 23501.docx**

ns and information exchange between systems - Local and metropolitan area networks - Specific requirements - Part 11: Wireless LAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications. [107] IEEE Std 1588-2008: IEEE Standard for a Precision Clock Synchronization Protocol for Networked Measurement and Control Systems. [108] 3GPP TS 28.552: Management and orchestration; 5G performance measurements. [109] 3GPP TS 24.193: Access Traffic Steering, Switching and Splitting; Stage 3. [110] 3GPP TS 24.526: User Equipment (UE) policies for 5G System (5GS); Stage 3. [111] 3GPP TS 22.186: Enhancement of 3GPP support for V2X scenarios; Stage 1. [112] 3GPP TR 38.824: Study on physical layer enhancements for NR ultra-reliable and low latency case (URLLC). [113] IEEE: Guidelines for Use of Extended Unique Identifier (EUI), Organizationally Unique Identifier (OUI) and Company ID (CID), https://standards.ieee.org/content/dam/ieee-standards/standards/web/documents/tutorials/eui.pdf. [114] 3GPP TS 32.256: Charging Management; 5G connection and mobility domain charging; Stage 2.

**[D5] 38300.docx**

and Functions The main services and functions of the PDCP sublayer include: - Transfer of data (user plane or control plane); - Maintenance of PDCP SNs; - Header compression and decompression using the ROHC protocol; - Header compression and decompression using EHC protocol; - Compression and decompression of uplink PDCP SDUs: DEFLATE based UDC only; - Ciphering and deciphering; - Integrity protection and integrity verification; - Timer based SDU discard; - For split bearers, routing; - Duplication; - Reordering and in-order delivery; - Out-of-order delivery; - Duplicate discarding. Since PDCP does not allow COUNT to wrap around in DL and UL, it is up to the network to prevent it from happening (e.g. by using a release and add of the corresponding radio bearer or a full configuration). ## 6.5 SDAP Sublayer The main services and functions of SDAP include: - Mapping between a QoS flow and a data radio bearer; NOTE: When remapping an XR QoS flow carrying PDU sets (see clause 16.15) from

## gs-009: What does the RRC protocol do in NR?

### Answer

The RRC protocol in NR is responsible for establishing and controlling RRC connections, which include paging, connection establishment, and security activation [D1]. 

RRC connection establishment involves the establishment of SRB1, and the procedure is also used to transfer the initial NAS dedicated information from the UE to the network [D1]. 

In NR sidelink communication/discovery, an RRC connection establishment is initiated only in the following cases: if configured by upper layers to transmit NR sidelink communication and related data is available for transmission, or if the frequency on which the UE is configured to transmit NR sidelink communication is included in sl-FreqInfoList/sl-FreqInfoListSizeExt [D5]. 

The RRC protocol also includes the broadcast of system information, including ETWS notification, CMAS notification, and positioning assistance data [D1]. 

However, the context does not provide enough information to determine the full scope of the RRC protocol's functions in NR.

### Context

**[D1] 36331.docx**

rovided by Medium Access Control layer (e.g. the logical channels) are provided in TS 36.321 [6]. The services provided by physical layer (e.g. the transport channels) are specified in TS 36.302 [3]. ## 4.4 Functions The RRC protocol includes the following main functions: - Broadcast of system information: - Including NAS common information; - Information applicable for UEs in RRC_IDLE, e.g. cell (re-)selection parameters, neighbouring cell information and information (also) applicable for UEs in RRC_CONNECTED, e.g. common channel configuration information; - Including ETWS notification, CMAS notification; - Including positioning assistance data. - RRC connection control: - Paging; - Establishment/ modification/ suspension / resumption / release of RRC connection, including e.g. assignment/ modification of UE identity (C-RNTI), establishment/ modification/ suspension/ resumption/ release of SRB1, SRB1bis, SRB2 and SRB4, access class barring; - Initial security activation, i.e.

**[D2] 38300.docx**

um Access Control (MAC) protocol specification. [7] 3GPP TS 38.322: NR; Radio Link Control (RLC) protocol specification. [8] 3GPP TS 38.323: NR; Packet Data Convergence Protocol (PDCP) specification. [9] 3GPP TS 37.324: E-UTRA and NR; Service Data Adaptation Protocol (SDAP) specification. [10] 3GPP TS 38.304: NR; User Equipment (UE) procedures in Idle mode and RRC Inactive state. [11] 3GPP TS 38.306: NR; User Equipment (UE) radio access capabilities. [12] 3GPP TS 38.331: NR; Radio Resource Control (RRC); Protocol specification. [13] 3GPP TS 38.133: NR; Requirements for support of radio resource management. [14] 3GPP TS 22.168: Earthquake and Tsunami Warning System (ETWS) requirements; Stage 1. [15] 3GPP TS 22.268: Public Warning System (PWS) Requirements. [16] 3GPP TS 38.410: NG-RAN; NG general aspects and principles. [17] 3GPP TS 38.420: NG-RAN; Xn general aspects and principles. [18] 3GPP TS 38.101-1: NR; User Equipment (UE) radio transmission and reception; Part 1: Range 1 Standalone. [19] 3GPP TS 22.261: Service requirements for next generation new services and markets.

**[D3] 36331.docx**

n the document. ## 1 Scope The present document specifies the Radio Resource Control protocol for the radio interface between UE and E-UTRAN as well as for the radio interface between RN and E-UTRAN. The scope of the present document also includes: - the radio related information transported in a transparent container between source eNB and target eNB upon inter eNB handover; - the radio related information transported in a transparent container between a source or target eNB and another system upon inter RAT handover. The RRC protocol is also used to configure the radio interface between an IAB-node and its parent nodes as specified in TS 38.300 [106]. ## 2 References The following documents contain provisions which, through reference in this text, constitute provisions of the present document. - References are either specific (identified by date of publication, edition number, version number, etc.) or non-specific. - For a specific reference, subsequent revisions do not apply. - For a non-specific reference, the latest version applies.

**[D4] 38413.docx**

OTOCOL-EXTENSION ::  ...  NR-CGIList :: SEQUENCE (SIZE(1..maxnoofCellsingNB)) OF NR-CGI NR-CGIListForWarning :: SEQUENCE (SIZE(1..maxnoofCellIDforWarning)) OF NR-CGI NR-PagingeDRXInformation :: SEQUENCE  nR-paging-eDRX-Cycle NR-Paging-eDRX-Cycle, nR-paging-Time-Window NR-Paging-Time-Window OPTIONAL, iE-Extensions ProtocolExtensionContainer  NR-PagingeDRXInformation-ExtIEs  OPTIONAL, ...  NR-PagingeDRXInformation-ExtIEs NGAP-PROTOCOL-EXTENSION ::  ...  NR-Paging-eDRX-Cycle :: ENUMERATED  hfquarter, hfhalf, hf1, hf2, hf4, hf8, hf16, hf32, hf64, hf128, hf256, hf512, hf1024, ...  NR-Paging-Long-eDRX-Information-for-RRC-INACTIVE :: SEQUENCE  nR-paging-Long-eDRX-Cycle-for-RRC-INACTIVE NR-Paging-Long-eDRX-Cycle-for-RRC-INACTIVE, nR-paging-Time-Window-for-RRC-INACTIVE NR-Paging-Time-Window-for-RRC-INACTIVE, iE-Extensions ProtocolExtensionContainer  NR-Paging-Long-eDRX-Information-for-RRC-INACTIVE-ExtIEs  OPTIONAL, ...  NR-Paging-Long-eDRX-Information-for-RRC-INACTIVE-ExtIEs NGAP-PROTOCOL-EXTENSION ::  ...

**[D5] 38331.docx**

stablish an RRC connection. RRC connection establishment involves SRB1 establishment. The procedure is also used to transfer the initial NAS dedicated information/ message from the UE to the network. The network applies the procedure e.g.as follows: - When establishing an RRC connection; - When UE is resuming or re-establishing an RRC connection, and the network is not able to retrieve or verify the UE context. In this case, UE receives RRCSetup and responds with RRCSetupComplete. ## 5.3.3.1a Conditions for establishing RRC Connection for NR sidelink communication/discovery/V2X sidelink communication/MP operation For NR sidelink communication/discovery, an RRC connection establishment is initiated only in the following cases: 1 if configured by upper layers to transmit NR sidelink communication and related data is available for transmission: 2 if the frequency on which the UE is configured to transmit NR sidelink communication is included in sl-FreqInfoList/sl-FreqInfoListSizeExt withi

## gs-010: How is QoS managed in NG-RAN and 5GC?

### Answer

QoS (Quality of Service) management in NG-RAN and 5GC involves a two-step mapping of IP-flows to QoS flows and from QoS flows to DRBs (Data Radio Bearers) [D1]. 

At the NAS (Non-Access Stratum) level, a QoS flow is characterized by a QoS profile provided by 5GC to NG-RAN and QoS rules provided by 5GC to the UE (User Equipment) [D1]. The QoS profile is used by NG-RAN to determine the treatment on the radio interface, while the QoS rules dictate the mapping between uplink User Plane traffic and QoS flows to the UE [D1].

The QoS flow may be either GBR (Guaranteed Bit Rate) or Non-GBR (Non-Guaranteed Bit Rate) depending on its profile [D1]. The QoS profile of a QoS flow contains QoS parameters, such as a 5G QoS Identifier (5QI) and an Allocation and Retention Priority (ARP) [D1].

In the QoS architecture in NG-RAN, packets belonging to different PDU (PDU Session) sessions are mapped to different DRBs [D2]. NAS-level packet filters in the UE and in the 5GC associate UL (Uplink) and DL (Downlink) packets with QoS Flows [D2]. AS-level mapping rules in the UE and in the NG-RAN associate UL and DL QoS Flows with DRBs [D2].

The 5G QoS Flow or QoS Flow is the finest granularity for QoS forwarding treatment in the 5G System, and all traffic mapped to the same 5G QoS Flow receives the same forwarding treatment [D3].

### Context

**[D1] 38300.docx**

d DL packets with QoS Flows; - AS-level mapping rules in the UE and in the NG-RAN associate UL and DL QoS Flows with DRBs. Figure 12-1: QoS architecture NG-RAN and 5GC ensure quality of service (e.g. reliability and target delay) by mapping packets to appropriate QoS Flows and DRBs. Hence there is a 2-step mapping of IP-flows to QoS flows (NAS) and from QoS flows to DRBs (Access Stratum). At NAS level, a QoS flow is characterised by a QoS profile provided by 5GC to NG-RAN and QoS rule(s) provided by 5GC to the UE. The QoS profile is used by NG-RAN to determine the treatment on the radio interface while the QoS rules dictates the mapping between uplink User Plane traffic and QoS flows to the UE. A QoS flow may either be GBR or Non-GBR depending on its profile. The QoS profile of a QoS flow contains QoS parameters, for instance (see TS 23.501 [3]): - For each QoS flow: - A 5G QoS Identifier (5QI); - An Allocation and Retention Priority (ARP).

**[D2] 38300.docx**

U session by a QoS Flow ID (QFI) carried in an encapsulation header over NG-U. The QoS architecture in NG-RAN, both for NR connected to 5GC and for E-UTRA connected to 5GC, is depicted in the Figure 12-1 and described in the following: - For each UE, 5GC establishes one or more PDU Sessions; - Except for NB-IoT, IAB-MT in SA mode, and NCR-MT, for each UE, the NG-RAN establishes at least one Data Radio Bearers (DRB) together with the PDU Session and additional DRB(s) for QoS flow(s) of that PDU session can be subsequently configured (it is up to NG-RAN when to do so); - If NB-IoT UE supports NG-U data transfer, the NG-RAN may establish Data Radio Bearers (DRB) together with the PDU Session and one PDU session maps to only one DRB; - The NG-RAN maps packets belonging to different PDU sessions to different DRBs; - NAS level packet filters in the UE and in the 5GC associate UL and DL packets with QoS Flows; - AS-level mapping rules in the UE and in the NG-RAN associate UL and DL QoS Flows with DRBs. Figure 12-1: QoS architecture NG-RAN and 5GC ensure quality of service (e.g.

**[D3] 23501.docx**

t is used by an NG-RAN to provide the 5GS time to the UE(s) over the radio interface using procedures specified in TS 38.331 [28]. 5G Core Network: The core network specified in the present document. It connects to a 5G Access Network. 5G LAN-Type Service: A service over the 5G system offering private communication using IP and/or non-IP type communications. 5G LAN-Virtual Network: A virtual network over the 5G system capable of supporting 5G LAN-type service. 5G NSWO: The 5G NSWO is the capability provided by 5G system and by UE to enable the connection to a WLAN access network using 5GS credentials without registration to 5GS. 5G QoS Flow or QoS Flow: The finest granularity for QoS forwarding treatment in the 5G System. All traffic mapped to the same 5G QoS Flow receive the same forwarding treatment (e.g. scheduling policy, queue management policy, rate shaping policy, RLC configuration, etc.). Providing different QoS forwarding treatment requires separate 5G QoS Flow. 5G QoS Identifier: A scalar that is used as a reference to a specific QoS forwarding behaviour (e.g.

**[D4] 38300.docx**

stem information; - Cell re-selection mobility; - Paging for mobile terminated data is initiated by 5GC; - Transfer of MBS broadcast data to the UE over MRB(s); - DRX for CN paging configured by NAS. - RRC_INACTIVE: - PLMN selection; - Broadcast of system information; - Cell re-selection mobility; - Paging is initiated by NG-RAN (RAN paging); - RAN-based notification area (RNA) is managed by NG- RAN; - DRX for RAN paging configured by NG-RAN; - 5GC - NG-RAN connection (both C/U-planes) is established for UE; - The UE Inactive AS context is stored in NG-RAN and the UE; - NG-RAN knows the RNA which the UE belongs to; - Transfer of MBS multicast/broadcast data to the UE over MRB(s); - Transfer of unicast data and/or signalling to/from the UE over radio bearers configured for SDT. - RRC_CONNECTED: - 5GC - NG-RAN connection (both C/U-planes) is established for UE; - The UE AS context is stored in NG-RAN and the UE; - NG-RAN knows the cell which the UE belongs to; - Transfer of unicast data

**[D5] 23501.docx**

N3IWF is supported as described in clause 5.7 and clause 4.12.5 of TS 23.502 [3]. QoS differentiation between UE and TNGF is supported as described in clause 5.7 and clause 4.12a.5 of TS 23.502 [3]. ## 4.2.8.1A General Concepts to support Wireline Access Wireline 5G Access Network (W-5GAN) shall be connected to the 5G Core Network via a Wireline Access Gateway Function (W-AGF). The W-AGF interfaces the 5G Core Network CP and UP functions via N2 and N3 interfaces, respectively. For the scenario of 5G-RG connected via NG RAN the specification for UE defined in this TS, TS 23.502 [3] and TS 23.503 [45] are applicable as defined for UE connected to 5GC via NG RAN unless differently specified in this TS and in TS 23.316 [84]. When a 5G-RG is connected via a NG-RAN and via a W-5GAN, multiple N1 instances shall exist for the 5G-RG i.e. there shall be one N1 instance over NG-RAN and one N1 instance over W-5GAN. A 5G-RG simultaneously connected to the same 5G Core Network of a PLMN over a 3GPP access and a W-5GAN access shall be served by a single AMF in this 5G Core Network.

## gs-012: What is PDCP and what functions does it perform in NR?

### Answer

The Packet Data Convergence Protocol (PDCP) is a protocol used in 5G New Radio (NR) networks, supporting functions such as header compression and decompression, data transfer, ciphering and deciphering, integrity protection and integrity verification, and timer-based SDU discard, among others [D1].

PDCP performs several key functions in NR, including header compression and decompression using the ROHC protocol, header compression and decompression using the EHC protocol, uplink data compression and decompression using the UDC protocol, ciphering and deciphering, integrity protection and integrity verification, and timer-based SDU discard [D1].

In NR, PDCP is used for both control plane and user plane data transfer, and it supports functions such as duplication, reordering, and in-order delivery of PDCP PDUs [D1].

For a NB-IoT UE that supports Control Plane CIoT EPS optimisation and S1-U data transfer or User Plane CIoT EPS optimisation, PDCP is not used until AS security is activated [D3]. 

Note that the provided context does not contain enough information to provide a comprehensive answer to the question.

### Context

**[D1] 38323.docx**

ransfer. ## 4.4 Functions The PDCP layer supports the following functions: - transfer of data (user plane or control plane); - maintenance of PDCP SNs; - header compression and decompression using the ROHC protocol; - header compression and decompression using the EHC protocol; - uplink data compression and decompression using the UDC protocol; - ciphering and deciphering; - integrity protection and integrity verification; - timer based SDU discard; - PDU Set discard; - PSI based SDU discard; - for split bearers and DAPS bearer, routing; - duplication; - reordering and in-order delivery; - out-of-order delivery; - duplicate discarding. ## 5 Procedures ## 5.1 PDCP entity handling ## 5.1.1 PDCP entity establishment When upper layers request a PDCP entity establishment for a radio bearer for Uu or PC5 interface; or for NR sidelink communication for groupcast and broadcast or for sidelink SRB4, when receiving the first PDCP PDU, and there is not yet a corresponding PDCP entity, the UE shal

**[D2] 36423.docx**

trial Radio Access (E-UTRA) and NR; Multi-connectivity; Stage 2. [33] 3GPP TS 38.323: NR; Packet Data Convergence Protocol (PDCP) specification. [34] 3GPP TS 38.401: NG-RAN; Architecture description. [35] IETF RFC 5905: Network Time Protocol Version 4: Protocol and Algorithms Specification. [36] 3GPP TS 26.247: Transparent end-to-end Packet-switched Streaming Service (PSS); Progressive Download and Dynamic Adaptive Streaming over HTTP (3GP-DASH). [37] 3GPP TS 38.104: NR; Base Station (BS) radio transmission and reception. [38] 3GPP TS 23.501: System Architecture for the 5G System [39] 3GPP TS 38.413: NG Radio Access Network (NG-RAN); NG Application Protocol (NGAP). [40] 3GPP TS 36.322: Evolved Universal Terrestrial Radio Access (E-UTRA); Radio Link Control (RLC) protocol specification. [41] 3GPP TS 23.285:  Technical Specification Group Services and System Aspects; Architecture enhancements for V2X services. [42] 3GPP TS 38.211: NR; Physical channels and modulation. [43] 3GPP TS 38.213: NR; Physical layer procedures for control.

**[D3] 36300.docx**

6.3, clause 6.2 and clause 6.1 respectively. NOTE 1: For a NB-IoT UE that only supports Control Plane CIoT 5GS Optimisation, as defined in TS 25.401 [91], PDCP is bypassed and DTCH is not supported. NOTE 2: For a NB-IoT UE that supports Control Plane CIoT 5GS Optimisation and NG-U data transfer or User Plane CIoT 5GS Optimisation, as defined in TS 25.401 [91], PDCP is also bypassed (i.e. not used) until AS security is activated. ## 24.2.2 Control Plane Except for NB-IoT, the figure below shows the protocol stack for the control plane, where: - NR PDCP sublayer (terminated in ng-eNB on the network side) performs the functions listed for the control plane in clause 6.4 of TS 38.300 [79]. The UE uses only NR PDCP for both SRBs and DRBs when connected to 5GC; - RLC and MAC sublayers (terminated in ng-eNB on the network side) perform the functions listed in clause 6.2 and 6.1; - RRC (terminated in ng-eNB on the network side) performs the functions listed in clause 7; - NAS control protocol

**[D4] 36323.docx**

m lower layers per RLC entity (for a detailed description see TS 36.322 [5]): - acknowledged data transfer service, including indication of successful delivery of PDCP PDUs; - unacknowledged data transfer service; - in-sequence delivery, except at re-establishment of lower layers; - duplicate discarding, except at re-establishment of lower layers. A PDCP entity expects the following services from the LWAAP entity (for a detailed description see TS 36.360 [15]): - user plane data transfer service; ## 4.4 Functions The Packet Data Convergence Protocol supports the following functions: - header compression and decompression of IP data flows using the ROHC protocol; - header compression and decompression of Ethernet data flows using the EHC protocol; - compression and decompression of uplink PDCP SDU; - transfer of data (user plane or control plane); - maintenance of PDCP SNs; - in-sequence delivery of upper layer PDUs at re-establishment of lower layers; - duplicate elimination of lower l

**[D5] 36300.docx**

s at PDCP re-establishment procedure for RLC AM; - Ciphering and deciphering; - Timer-based SDU discard in uplink. NOTE 1: When compared to UTRAN, the lossless DL RLC PDU size change is not required. The main services and functions of the PDCP for the control plane include: - Ciphering and Integrity Protection; - Transfer of control plane data. Except for NB-IoT, the main services and functions of the PDCP sublayer for the control plane also include: - Duplication of PDCP PDUs; - For PDCP duplication, reordering and duplicate detection at the receiver. NOTE 2: For a NB-IoT UE that only supports Control Plane CIoT EPS optimisation, as defined in TS 24.301 [20], PDCP is bypassed. For a NB-IoT UE that supports Control Plane CIoT EPS optimisation and S1-U data transfer or User Plane CIoT EPS optimisation, as defined in TS 24.301 [20], PDCP is not used until AS security is activated. ## 6.3.2 PDU Structure Figure 6.3.2-1 below depicts the PDCP PDU structure for user plane data, where: - PDCP PDU and PDCP header are octet-aligned; - PDCP header can be either 1 , 2 or 5 bytes long.

## gs-014: What are the gNB-CU-CP and gNB-CU-UP and how do they differ?

### Answer

The gNB-CU-CP and gNB-CU-UP are logical nodes in the gNB (5G New Radio) architecture.

The gNB-CU-CP (gNB Control-User Plane Component) is a logical node hosting the control plane part of the PDCP (Packet Data Convergence Protocol) protocol of the gNB-CU (5G New Radio User Plane) for an eNB (Evolved-NodeB) or a gNB acting as secondary node [D2]. It terminates the E1 interface connected with the gNB-CU-UP and the F1-C interface connected with the gNB-DU [D2].

The gNB-CU-UP (gNB Control-User Plane User Plane) is a logical node hosting the user plane part of the PDCP protocol of the gNB-CU for an eNB, and the user plane part of the PDCP protocol and the SDAP (Session Description Protocol) protocol of the gNB-CU for a gNB [D2]. It terminates the E1 interface connected with the gNB-CU-CP and the F1-U interface connected with the gNB-DU [D2].

The main difference between the gNB-CU-CP and gNB-CU-UP is that the gNB-CU-CP is responsible for the control plane, while the gNB-CU-UP is responsible for the user plane [D2].

### Context

**[D1] 38401.docx**

d to only one gNB-CU-CP; - One gNB-CU-UP is connected to only one gNB-CU-CP; NOTE 1: For resiliency, a gNB-DU and/or a gNB-CU-UP may be connected to multiple gNB-CU-CPs by appropriate implementation. - One gNB-DU can be connected to multiple gNB-CU-UPs under the control of the same gNB-CU-CP; - One gNB-CU-UP can be connected to multiple DUs under the control of the same gNB-CU-CP; NOTE 2: The connectivity between a gNB-CU-UP and a gNB-DU is established by the gNB-CU-CP using Bearer Context Management functions. NOTE 3: The gNB-CU-CP selects the appropriate gNB-CU-UP(s) for the requested services for the UE. In case of multiple CU-UPs they belong to same security domain as defined in TS 33.210 [18]. NOTE 4: Data forwarding between gNB-CU-UPs during intra-gNB-CU-CP handover within a gNB may be supported by Xn-U. ## 6.1.3 Overall Architecture of IAB Figure 6.1.3-1: Overall architecture of IAB The NG-RAN supports IAB by the IAB-node wirelessly connecting to the gNB capable of serving the IAB-nodes, named IAB-donor.

**[D2] 38401.docx**

of an en-gNB or a gNB acting as secondary node. gNB-CU-Control Plane (gNB-CU-CP): a logical node hosting the RRC and the control plane part of the PDCP protocol of the gNB-CU for an en-gNB or a gNB. The gNB-CU-CP terminates the E1 interface connected with the gNB-CU-UP and the F1-C interface connected with the gNB-DU. For DC operation, the MgNB-CU-CP designates the gNB-CU-CP of the gNB-CU for an en-gNB or a gNB acting as master node, and the SgNB-CU-CP designates the gNB-CU-CP of the gNB-CU for an en-gNB or a gNB acting as secondary node. gNB-CU-User Plane (gNB-CU-UP): a logical node hosting the user plane part of the PDCP protocol of the gNB-CU for an en-gNB, and the user plane part of the PDCP protocol and the SDAP protocol of the gNB-CU for a gNB. The gNB-CU-UP terminates the E1 interface connected with the gNB-CU-CP and the F1-U interface connected with the gNB-DU. For DC operation, the MgNB-CU-UP designates the gNB-CU-UP of the gNB-CU for an en-gNB or a gNB acting as master node,

**[D3] 38401.docx**

CU-CP respectively using a configured TNL address. NOTE 1: The gNB-CU-UP/gNB-CU-CP may use different source and/or destination IP end point(s) if the TNL establishment towards one IP end point fails. How the gNB-CU-UP/gNB-CU-CP gets the remote IP end point(s) and its own IP address are outside the scope of this specification. 2-3 (A). Once the TNLA (gNB-CU-UP initiated) has been established, the gNB-CU-UP initiates the E1 Setup procedure to exchange application level configuration data. 2-3 (B). Once the TNLA (gNB-CU-CP initiated) has been established, the gNB-CU-CP initiates the E1 Setup procedure to exchange application level configuration data. 4-6. The gNB-CU-CP may add additional SCTP Endpoint(s) to be used for E1 signalling between the gNB-CU-CP and the gNB-CU-UP pair using the gNB-CU-CP Configuration Update procedure. The gNB-CU-CP Configuration Update procedure also allows the gNB-CU-CP to request the gNB-CU-UP to modify or release TNLA(s). 7-9.

**[D4] 38401.docx**

g-eNB-DU(s). An ng-eNB-CU-CP and an ng-eNB-CU-UP is connected via the E1 interface. An ng-eNB-DU is connected to an ng-eNB-CU-CP via the W1-C interface, and to an ng-eNB-CU-UP via the W1-U interface. The general principle described in this clause also applies to ng-eNB and its corresponding E1 and W1 interfaces, if not explicitly specified otherwise. Figure 6.1.2-1. Overall architecture for separation of gNB-CU-CP and gNB-CU-UP - A gNB may consist of a gNB-CU-CP, multiple gNB-CU-UPs and multiple gNB-DUs; - The gNB-CU-CP is connected to the gNB-DU through the F1-C interface; - The gNB-CU-UP is connected to the gNB-DU through the F1-U interface; - The gNB-CU-UP is connected to the gNB-CU-CP through the E1 interface; - One gNB-DU is connected to only one gNB-CU-CP; - One gNB-CU-UP is connected to only one gNB-CU-CP; NOTE 1: For resiliency, a gNB-DU and/or a gNB-CU-UP may be connected to multiple gNB-CU-CPs by appropriate implementation.

**[D5] 38401.docx**

CU-CP sends NGAP Broadcast Session Setup Response towards 5GC2. Afterwards, if the gNB-CU-CP decides (e.g., in case the 5GC1 triggers Broadcast Session Release) to establish shared NG-U resources with the 5GC2 with which the shared NG-U was not established: - in case of multicast transport, the gNB-CU-CP triggers BC Bearer Context Modification Request towards the gNB-CU-UP providing the stored multicast address received from the 5GC2. Then the gNB-CU-UP joins the NG-U multicast group of 5GC2 accordingly; - in case of unicast transport, the gNB-CU-CP triggers Broadcast Session Transport Request towards the core network providing the unicast transport address received from the gNB-CU-UP. NOTE: The gNB CU-UP may support PDCP SN continuity after establishment of shared NG-U resources with 5GC2. ## 8.15.1.1b Broadcast MBS Session Setup for resource efficiency for RAN sharing with multiple cell-ID broadcast Figure 8.15.1.1b-1 illustrates an exemplified interaction of NGAP, E1AP, F1AP and RRC

## gs-015: What is beamforming and beam management in 5G NR?

### Answer

Beamforming in 5G NR refers to the process of directing radio energy from an antenna to a specific user equipment (UE) device, improving signal strength and reducing interference. This is achieved by adjusting the phase and amplitude of the radio signals transmitted by the base station (gNB) to match the direction of the UE's antenna. [D3]

Beam management in 5G NR is a related concept that involves the selection and optimization of the beamforming process to improve the overall performance of the wireless communication system. This includes tasks such as beam selection, beam tracking, and beam switching, which are performed by the gNB to adapt to changes in the UE's location and movement. [D3]

AI/ML-based beam management utilizes intra-cell downlink beam prediction of the serving cell to reduce measurement/RS overhead and to improve the accuracy of beam selection. [D3]

There is no clear definition of beamforming and beam management in the provided context documents. The provided information seems to be related to beam prediction and beam tracking, but it does not explicitly define beamforming and beam management.

### Context

**[D1] 38211.docx**

s to NR support for dedicated spectrum less than 5MHz for FR1 | 18.1.0 2023-12 | RAN#102 | RP-233705 | 0117 | - | F | Corrections to MIMO enhancements | 18.1.0 2023-12 | RAN#102 | RP-233718 | 0118 | - | F | Corrections to NR Network-controlled Repeaters | 18.1.0 2023-12 | RAN#102 | RP-233719 | 0119 | - | F | Corrections to positioning enhancements | 18.1.0 2023-12 | RAN#102 | RP-233733 | 0120 | - | B | Introduction of multicast reception in RRC_INACTIVE | 18.1.0 2024-03 | RAN#103 | RP-240518 | 0122 | - | F | Corrections to MIMO enhancements | 18.2.0 2024-03 | RAN#103 | RP-240528 | 0123 | - | F | Corrections to positioning enhancements | 18.2.0 2024-03 | RAN#103 | RP-240535 | 0125 | - | A | Alignment of parameter names | 18.2.0 2024-03 | RAN#103 | RP-240519 | 0126 | - | F | Corrections to sidelink enhancements | 18.2.0 2024-06 | RAN#104 | RP-241061 | 0127 | - | F | Correction for hop counting in SRS for positioning with tx hopping | 18.3.0 2024-06 | RAN#104 | RP-241075 | 0128 | - | F |

**[D2] 38214.docx**

ntroduction of Multi-carrier enhancements for NR Phase 3 | 19.0.0 2025-06 | RAN#108 | RP-251580 | 0676 | - | B | Introduction of 3Tx UL enhancements and asymmetric UL mTRP operation for NR MIMO Phase 5 | 19.0.0 2025-06 | RAN#108 | RP-251580 | 0677 | - | B | Introduction of CSI enhancements for NR MIMO Phase 5 | 19.0.0 2025-06 | RAN#108 | RP-251580 | 0678 | - | B | Introduction of UE-initiated/event-driven beam management | 19.0.0 2025-06 | RAN#108 | RP-251582 | 0679 | - | B | Introduction of specification support for NR mobility enhancements phase 4 | 19.0.0 2025-06 | RAN#108 | RP-251583 | 0680 | - | B | Introduction of specification support for NR_NTN_Ph3 functionality | 19.0.0 2025-06 | RAN#108 | RP-251571 | 0688 | - | B | Introduction of enhancements of network energy savings | 19.0.0 2025-09 | RAN#109 | RP-252634 | 0681 | 1 | B | TEI19 Counting of CSI-RS resource referred by N CSI reporting settings [SimCSI_count] | 19.1.0 2025-09 | RAN#109 | RP-252634 | 0682 | 1 | B | TEI19 Combin

**[D3] 38300.docx**

ed by the session stop indication. The gNB includes time stamp information to the QoE measurement reports to enable the correlation of corresponding measurement results of MDT and QoE at the MCE/TCE. In addition, the gNB includes the MDT session identifiers (Trace Reference and Trace Recording Session Reference) in the corresponding QoE measurement report. ## 21.6 QoE Measurement Collection in High Mobility Scenarios QoE measurements can be confined to high mobility state of the UE and/or to HSDN cells. ## 21.7 Void ## 22 Support of AI/ML for NR Air Interface ## 22.1 Overview The objective of AI/ML for NR air interface is to improve network performance and user experience, through AI/ML-enabled enhancements to the following features: beam management, CSI prediction and positioning. ## 22.2 AI/ML-based Beam Management ## 22.2.1 Introduction AI/ML-based beam management utilizes intra-cell downlink beam prediction of the serving cell to reduce measurement/RS overhead and to improve the accuracy of beam selection.

**[D4] 23401.docx**

Radio Access (E-UTRA); User Equipment (UE) radio access capabilities. [83] 3GPP TS 23.501: System Architecture for the 5G System; Stage 2. [84] 3GPP TS 23.502: Procedures for the 5G System; Stage 2. [85] 3GPP TS 37.340: Evolved Universal Terrestrial Radio Access (E-UTRA) and NR; Multi-connectivity; Stage 2. [86] 3GPP TS 29.002: Mobile Application Part (MAP) specification. [87] 3GPP TS 36.321: Evolved Universal Terrestrial Radio Access -E-UTRA); Medium Access Control -MAC) protocol specification. [88] 3GPP TS 23.503: Policy and Charging Control Framework for the 5G System; Stage 2. [89] 3GPP TS 38.331: NR; Radio Resource Control (RRC); Protocol specification. [90] 3GPP TS 38.401: NG-RAN; Architecture description. [91] 3GPP TS 29.674: Interface between the UE radio Capability Management Function (UCMF) and the Mobility Management Entity (MME); Stage 3. [92] 3GPP TS 36.410: Evolved Universal Terrestrial Radio Access Network (E-UTRAN); S1 general aspects and principles. [93] 3GPP TS 38.300: NR; NR and NG-RAN Overall Description; Stage 2.

**[D5] 38300.docx**

rt Channel. This should be clearly separated from the classification of what is transported, which relates to the concept of logical channels at MAC sublayer. Downlink transport channel types are: 1. Broadcast Channel (BCH) characterised by: - fixed, pre-defined transport format; - requirement to be broadcast in the entire coverage area of the cell, either as a single message or by beamforming different BCH instances. 2. Downlink Shared Channel (DL-SCH) characterised by: - support for HARQ; - support for dynamic link adaptation by varying the modulation, coding and transmit power; - possibility to be broadcast in the entire cell; - possibility to use beamforming; - support for both dynamic and semi-static resource allocation; - support for UE discontinuous reception (DRX) to enable UE power saving. 3. Paging Channel (PCH) characterised by: - support for UE discontinuous reception (DRX) to enable UE power saving (DRX cycle is indicated by the network to the UE); - requirement to be broa

## gs-016: What is dual connectivity in NR and how does it work?

### Answer

Dual connectivity in NR involves two RAN nodes, i.e. Master and Secondary RAN nodes, in providing radio resources to a given UE (with active radio bearers), while a single S1-MME termination point exists for an UE between a MME and the E-UTRAN [D4]. 

In this context, the Master RAN node performs all necessary N2 related functions such as mobility management, relaying of NAS signalling, etc. and manages the handling of user plane connection (e.g. transfer over N3) [D5]. The Master RAN node may use resources of another RAN node, the Secondary RAN node, to exchange User Plane traffic of an UE [D5]. 

Dual connectivity defines Master Cell Group (MCG) bearer and Secondary Cell Group (SCG) bearer alternatives [D4]. For E-RABs configured as MCG bearers the U-plane termination points are maintained, whereas for E-RABs configured as SCG bearers it enables changing the U-plane termination point in the E-UTRAN by means of S1-MME signalling without changing the S1-MME termination point [D4]. 

However, the Dual Connectivity function does not apply to the NR RedCap UE [D5].

### Context

**[D1] 23501.docx**

nd UP integrity protection of the User Plane Security Enforcement information not set to Required, are allowed to be handed over to EPS regardless of how UP confidentiality protection applies in EPS. In the case of dual connectivity, the Integrity Protection is set to Preferred, the Master RAN node may notify the SMF when it cannot fulfil a User Plane Security Enforcement with a value of Preferred. The SMF handling of the PDU session with respect to the Integrity Protection status is up to SMF implementation decision. ## 5.11 Support for Dual Connectivity, Multi-Connectivity ## 5.11.1 Support for Dual Connectivity Dual Connectivity involves two radio network nodes in providing radio resources to a given UE (with active radio bearers), while a single N2 termination point exists for the UE between an AMF and the RAN. The RAN architecture and related functions to support Dual Connectivity is further described in RAN specifications (e.g. TS 37.340 [31]). In this Release of the specification, the Dual Connectivity function does not apply to the NR RedCap UE.

**[D2] 38331.docx**

imization of Drive Tests MIB Master Information Block MO-SDT Mobile Originated SDT MPE Maximum Permissible Exposure MP Multi-path MR Main Receiver MRB MBS Radio Bearer MR-DC Multi-Radio Dual Connectivity MTCH MBS Traffic Channel MT-SDT Mobile Terminated SDT MTSI Multimedia Telephony Service for IMS MUSIM Multi-Universal Subscriber Identity Module N3C Non-3GPP Connection N/A Not Applicable NCC Next Hop Chaining Counter NCR Network-Controlled Repeater NCR-Fwd NCR Forwarding NCR-MT NCR Mobile Termination NE-DC NR E-UTRA Dual Connectivity NES Network Energy Savings (NG)EN-DC E-UTRA NR Dual Connectivity (covering E-UTRA connected to EPC or 5GC) NGEN-DC E-UTRA NR Dual Connectivity with E-UTRA connected to 5GC NID Network Identifier NPN Non-Public Network NR-DC NR-NR Dual Connectivity NR/5GC NR connected to 5GC NSAG Network Slice AS Group NTN Non-Terrestrial Network OD-SIB1 On-demand SIB1 OD-SSB On-demand SSB OOK On-Off Keying PCell Primary Cell PDCP Packet Data Convergence Protocol PDU Proto

**[D3] 23401.docx**

: Typically, the MME and SGW cannot determine whether the RAN termination point(s) for the S1-U interface are located on a Master RAN node that has multiple IP addresses, or, on a Secondary RAN node. If the UE has indicated support for Dual Connectivity with NR and MME has an Access Restriction for NR for a UE (either signalled from the HSS, or, locally generated by VPLMN policy in the MME) then the MME shall signal this to the E-UTRAN as part of Handover Restriction List and to the UE in Attach and TAU Accept as defined in clauses 5.5.2.2.3, 5.5.2.4.3, 5.3.2.1, 5.3.3.1, 5.3.3.2 and D.3.6 respectively. An eNodeB supporting Dual Connectivity with NR checks whether the UE is allowed to use NR. If the UE is not allowed to use NR, the eNodeB shall not establish Dual Connectivity with NR as a secondary RAT. The MME uses UE support for dual connectivity with NR for SGW and PGW selection when the UE indicates support for NR and there is no Access Restriction for NR for the UE.

**[D4] 23401.docx**

of making available certain information and providing that information to a law enforcement monitoring facility. ## 4.3.2a Support for Dual Connectivity Dual Connectivity involves two RAN nodes, i.e. Master and Secondary RAN nodes (see TS 36.300 [5] for the definitions), in providing radio resources to a given UE (with active radio bearers), while a single S1-MME termination point exists for an UE between a MME and the E-UTRAN. The E-UTRAN architecture and related functions to support Dual Connectivity with E-UTRAN is further described in TS 36.300 [5]. Dual Connectivity with E-UTRAN as Master RAN node and NR as Secondary RAN node is further described in TS 37.340 [85]. Dual connectivity defines Master Cell Group (MCG) bearer and Secondary Cell Group (SCG) bearer alternatives (see TS 36.300 [5]). For E-RABs configured as MCG bearers the U-plane termination points are maintained, whereas for E-RABs configured as SCG bearers it enables changing the U-plane termination point in the E-UTRAN by means of S1-MME signalling without changing the S1-MME termination point.

**[D5] 23501.docx**

to support Dual Connectivity is further described in RAN specifications (e.g. TS 37.340 [31]). In this Release of the specification, the Dual Connectivity function does not apply to the NR RedCap UE. The RAN node at which the N2 terminates, performs all necessary N2 related functions such as mobility management, relaying of NAS signalling, etc. and manages the handling of user plane connection (e.g. transfer over N3). It is called the Master RAN Node. It may use resources of another RAN node, the Secondary RAN node, to exchange User Plane traffic of an UE. Master RAN node takes into account the RSN and/or PDU Session Pair ID to determine if dual connectivity shall be set up and ensure appropriate PDU session handling ensures fully redundant user plane path as described in clause 5.33.2.1. If the UE has Mobility Restriction (either signalled from the UDM, or, locally generated by the Serving PLMN policy in the AMF) the AMF signals these restrictions to the Master RAN Node as Mobility Restriction List; This may prevent the Master RAN node from setting up a Dual Connectivity for an UE.

## gs-017: What is HARQ in NR and how does it work?

### Answer

HARQ (Hybrid Automatic Repeat Request) is a retransmission mechanism used in 5G New Radio (NR) to improve the reliability of data transmission. In NR, HARQ is used to retransmit data that has been lost or corrupted during transmission, allowing the receiver to recover the original data.

HARQ works by maintaining a buffer of data at the transmitter and receiver, and using a sequence of redundancy versions to ensure that the received data is accurate. The HARQ process is associated with a HARQ buffer, which is used to store the data being transmitted. The HARQ process also maintains a state variable CURRENT_TX_NB, which indicates the number of transmissions that have taken place for the MAC PDU currently in the buffer, and a state variable HARQ_FEEDBACK, which indicates the HARQ feedback for the MAC PDU currently in the buffer [D1].

When the HARQ process is established, CURRENT_TX_NB is initialized to 0. The sequence of redundancy versions is 0, 2, 3, 1, and the variable CURRENT_IRV is an index into the sequence of redundancy versions, which is updated modulo 4 [D1].

The HARQ process can be configured to operate in different modes, including synchronous and asynchronous modes. In synchronous mode, the HARQ process is synchronized with the transmission of the MAC PDU, and the HARQ feedback is used to determine whether the data has been received correctly. In asynchronous mode, the HARQ process is not synchronized with the transmission of the MAC PDU, and the HARQ feedback is used to determine whether the data has been received correctly [D2].

The HARQ process can also be configured to use different retransmission strategies, including non-adaptive and adaptive retransmission. Non-adaptive retransmission involves retransmitting the same data packet, while adaptive retransmission involves retransmitting a new packet with a different redundancy version [D2].

In NR, the HARQ process is used in conjunction with the RLC (Radio Link Control) protocol to provide reliable data transmission. The RLC protocol is used to manage the transmission of data between the UE and the eNodeB, and the HARQ process is used to retransmit data that has been lost or corrupted during transmission [D3].

Overall, HARQ is an important mechanism in NR that provides reliable data transmission and improves the overall performance of the system.

### Context

**[D1] 36321.docx**

a transmission of another HARQ process scheduled using Short Processing Time: - instruct the identified HARQ process to generate a positive acknowledgement (ACK) of the data in the corresponding TB. When determining if NDI has been toggled compared to the value in the previous transmission the MAC entity shall ignore NDI received in all uplink grants on PDCCH for its Temporary C-RNTI and PUR-RNTI. ## 5.4.2.2 HARQ process Each HARQ process is associated with a HARQ buffer. For synchronous HARQ, each HARQ process shall maintain a state variable CURRENT_TX_NB, which indicates the number of transmissions that have taken place for the MAC PDU currently in the buffer, and a state variable HARQ_FEEDBACK, which indicates the HARQ feedback for the MAC PDU currently in the buffer. When the HARQ process is established, CURRENT_TX_NB shall be initialized to 0. The sequence of redundancy versions is 0, 2, 3, 1. The variable CURRENT_IRV is an index into the sequence of redundancy versions. This variable is up-dated modulo 4.

**[D2] 36321.docx**

operation is asynchronous or HARQ_FEEDBACK  NACK: - if both skipUplinkTxSPS and fixedRV-NonAdaptive are configured and the uplink grant of the initial transmission of this HARQ process was performed on a configured grant and UL HARQ operation is not autonomous; or - if the uplink grant is a preallocated uplink grant: - set CURRENT_IRV to 0; - else if UL HARQ operation is autonomous: - set CURRENT_IRV to the index corresponding to the redundancy version value selected by the UE implementation. - generate a transmission as described below. NOTE 1: When receiving a HARQ ACK alone, the MAC entity keeps the data in the HARQ buffer. NOTE 2: When no UL-SCH transmission can be made due to the occurrence of a measurement gap or a Sidelink Discovery Gap for Transmission, or prioritization of V2X sidelink communication transmission described in clause 5.14.1.2.2, no HARQ feedback can be received and a non-adaptive retransmission follows. NOTE 3: For asynchronous HARQ operation, UL retransmissions are triggered only by adaptive retransmission grants, except for retransmissions within a bundle.

**[D3] 38322.docx**

on has been produced by the 3rd Generation Partnership Project (3GPP). The contents of the present document are subject to continuing work within the TSG and may change following formal TSG approval. Should the TSG modify the contents of the present document, it will be re-released by the TSG with an identifying change of release date and an increase in version number as follows: Version x.y.z where: x the first digit: 1 presented to TSG for information; 2 presented to TSG for approval; 3 or greater indicates TSG approved document under change control. y the second digit is incremented for all changes of substance, i.e. technical enhancements, corrections, updates, etc. z the third digit is incremented when editorial only changes have been incorporated in the document. ## 1 Scope The present document specifies the NR Radio Link Control (RLC) protocol for the UE  NR radio interface. ## 2 References The following documents contain provisions which, through reference in this text, constitute provisions of the present document.

**[D4] 38212.docx**

I CG - Uplink Control Information CLI-RSSI Cross Link Interference  Received Signal Strength Indicator CORESET Control Resource Ret COT Channel Occupancy Time CP Cyclic Prefix CQI Channel Quality Indicator CRC Cyclic Redundancy Check CRI CSI-RS Resource Indicator CSI Channel State Information CSI-PAI CSI Prediction Accuracy Indicator CSI-RS CSI - Reference Signal DAI Downlink Assignment Index DCI Downlink Control Information DL Downlink DL-SCH Downlink - Shared Channel DMRS Demodulation Reference Signal HARQ Hybrid Automatic repeat Request HARQ-ACK Hybrid Automatic repeat Request - Acknowledgement LDPC Low Density Parity Check LI Layer Indicator MBS Multicast Broadcast Services MCS Modulation and Coding Scheme MRI Measurement Resource Index NCR Network-controlled repeater OFDM Orthogonal Frequency Division Multiplex PBCH Physical Broadcast Channel PCH Paging Channel PDCCH Physical Downlink Control Channel PDSCH Physical Downlink Shared Channel PMI Precoding Matrix Indicator PRB Physica

**[D5] 38321.docx**

smission starts is derived from the following equation: HARQ Process ID  [floor (CURRENT_slot  10 / (numberOfSlotsPerFrame  periodicity))] modulo nrofHARQ-Processes where CURRENT_slot  [(SFN  numberOfSlotsPerFrame)  slot number in the frame] and numberOfSlotsPerFrame refers to the number of consecutive slots per frame as specified in TS 38.211 [8]. For configured downlink assignments with harq-ProcID-Offset, the HARQ Process ID associated with the slot where the DL transmission starts is derived from the following equation: HARQ Process ID  [floor (CURRENT_slot  10 / (numberOfSlotsPerFrame  periodicity))] modulo nrofHARQ-Processes  harq-ProcID-Offset where CURRENT_slot  [(SFN  numberOfSlotsPerFrame)  slot number in the frame] and numberOfSlotsPerFrame refers to the number of consecutive slots per frame as specified in TS 38.211 [8]. NOTE 1: In case of unaligned SFN across carriers in a cell group, the SFN of the concerned Serving Cell is used to calculate the HARQ Process ID used for configured downlink assignments.

## gs-018: What is the RLC protocol in NR and what are its three modes?

### Answer

The RLC (Radio Link Control) protocol in NR supports three transmission modes: Transparent Mode (TM), Unacknowledged Mode (UM), and Acknowledged Mode (AM). 

The RLC configuration is per logical channel with no dependency on numerologies and/or transmission durations, and ARQ can operate on any of the numerologies and/or transmission durations the logical channel is configured with, [D3]. 

For SRB0, paging and broadcast system information, TM mode is used, while for other SRBs AM mode is used, [D3]. 

The main services and functions of the RLC sublayer depend on the transmission mode and include: transfer of upper layer PDUs, sequence numbering independent of the one in PDCP (UM and AM), and error correction through ARQ, [D3]. 

However, the specific details of the three modes (TM, UM, and AM) and their characteristics are not explicitly stated in the provided context excerpts.

### Context

**[D1] 38300.docx**

R sidelink communication may be used to support other services than V2X services. NR sidelink communication can support one of three types of transmission modes for a pair of a Source Layer-2 ID and a Destination Layer-2 ID in the AS: - Unicast transmission, characterized by: - Support of one PC5-RRC connection between peer UEs for the pair; - Transmission and reception of control information and user traffic between peer UEs in sidelink; - Support of sidelink HARQ feedback; - Support of sidelink transmit power control; - Support of RLC AM; - Detection of radio link failure for the PC5-RRC connection. - Groupcast transmission, characterized by: - Transmission and reception of user traffic among UEs belonging to a group in sidelink; - Support of sidelink HARQ feedback. - Broadcast transmission, characterized by: - Transmission and reception of user traffic among UEs in sidelink. ## 16.9.2 Radio Protocol Architecture for NR sidelink communication ## 16.9.2.1 Overview The AS protocol stac

**[D2] 36322.docx**

.1 2015-03 | RP-67 | RP-150376 | 0105 | 1 | | RLC concatenation for extended LI field | 12.2.0 | RP-67 | RP-150374 | 0107 | - | | Introduction of ProSe Direct Communication | 12.2.0 2015-09 | RP-69 | RP-151441 | 0108 | - | | Corrections for STCH in 36.322 | 12.3.0 2015-12 | RP-70 | RP-152071 | 0114 | - | | Introduction of extended RLC protocol formats for CA enhancement | 13.0.0 | RP-70 | RP-152080 | 0115 | - | | Introduction of SC-PTM in RLC | 13.0.0 2016-03 | RP-71 | RP-160470 | 0116 | 1 | | Clarification on Polling for last data | 13.1.0 2016-06 | RP-72 | RP-161078 | 0120 | 1 | | Addition of sidelink in the overview model | 13.2.0 | RP-72 | RP-161081 | 0121 | 2 | | Introduction of NB-IoT | 13.2.0 2017-03 | RP-75 | RP-170655 | 0126 | - | F | Correction on channel bandwidth definition for NB-IoT | 13.3.0 | RP-75 | RP-170637 | 0125 | 2 | B | Introducing Rel-14 NB-IoT enhancements into RLC | 14.0.0 2017-09 | RP-77 | RP-171914 | 0127 | 2 | C | Packet Reordering for Sidelink | 14.1.0 | RP

**[D3] 38300.docx**

yer is not configured for downlink/uplink spatial multiplexing, and when the physical layer is configured for downlink/uplink spatial multiplexing, a single HARQ process supports one or multiple TBs. ## 6.3 RLC Sublayer ## 6.3.1 Transmission Modes The RLC sublayer supports three transmission modes: - Transparent Mode (TM); - Unacknowledged Mode (UM); - Acknowledged Mode (AM). The RLC configuration is per logical channel with no dependency on numerologies and/or transmission durations, and ARQ can operate on any of the numerologies and/or transmission durations the logical channel is configured with. For SRB0, paging and broadcast system information, TM mode is used. For other SRBs AM mode used. For DRBs, either UM or AM mode are used. ## 6.3.2 Services and Functions The main services and functions of the RLC sublayer depend on the transmission mode and include: - Transfer of upper layer PDUs; - Sequence numbering independent of the one in PDCP (UM and AM); - Error Correction through AR

**[D4] 36331.docx**

.0 | RP-60 | RP-130804 | 1303 | 1 | | Clarification on inclusion of non-CA band combinations | 11.4.0 | RP-60 | RP-130809 | 1308 | - | | CR on ROHC parameter configuration in Rel-11 RRC | 11.4.0 | RP-60 | RP-130804 | 1315 | 2 | | Clarification on UE CA capability | 11.4.0 | RP-60 | RP-130809 | 1321 | - | | Updating 3GPP2 specification references | 11.4.0 | RP-60 | RP-130805 | 1323 | - | | Clarification on the configuration of the extended PHR | 11.4.0 | RP-60 | RP-130805 | 1324 | - | | Clarifications on SystemTimeInfoCDMA2000 IE | 11.4.0 | RP-60 | RP-130808 | 1325 | - | | MFBI impact on MBMS service continuity | 11.4.0 | RP-60 | RP-130819 | 1329 | 1 | | MFBI aspects for dedicated signalling | 11.4.0 09/2013 | RP-61 | RP-131311 | 1335 | - | | Clarification on PhysCellIdRange | 11.5.0 | RP-61 | RP-131311 | 1339 | 1 | | Correction on the first subframe of the measurement gap | 11.5.0 | RP-61 | RP-131319 | 1340 | 1 | | Correction for MFBI in SIB15 and SIB6 | 11.5.0 | RP-61 | RP-131319 | 13

**[D5] 38322.docx**

Control (RLC) protocol for the UE  NR radio interface. ## 2 References The following documents contain provisions which, through reference in this text, constitute provisions of the present document. - References are either specific (identified by date of publication, edition number, version number, etc.) or non-specific. - For a specific reference, subsequent revisions do not apply. - For a non-specific reference, the latest version applies. In the case of a reference to a 3GPP document (including a GSM document), a non-specific reference implicitly refers to the latest version of that document in the same Release as the present document. [1] 3GPP TR 21.905: Vocabulary for 3GPP Specifications. [2] 3GPP TS 38.300: NR Overall Description; Stage 2. [3] 3GPP TS 38.321: NR MAC protocol specification. [4] 3GPP TS 38.323: NR PDCP specification. [5] 3GPP TS 38.331: NR RRC Protocol specification. [6] 3GPP TS 23.287: Architecture enhancements for 5G System (5GS) to support Vehicle-to-Everything (V2X) services. [7] 3GPP TS 38.340: NR; Backhaul Adaptation Protocol (BAP) specification.

## gs-019: How does NR handle random access — what is the RACH procedure?

### Answer

The NR random access procedure is outlined in TS 38.300 [D2]. The three steps of the non-contention based random access procedure are: 

1) Random Access Preamble assignment via dedicated signalling in DL: 
- eNB assigns to UE a non-contention Random Access Preamble (a Random Access Preamble not within the set sent in broadcast signalling). 
- Signalled via: 
  - HO command generated by target eNB and sent via source eNB for handover; 
  - PDCCH in case of DL data arrival or positioning; 
  - PDCCH for initial UL time alignment for a sTAG. 
2) Random Access Preamble on RACH in uplink: 
- UE transmits the assigned non-contention Random Access Preamble. 
3) Random Access Response on DL-SCH: 
- Semi-synchronous (within a flexible window of which the size is two or more TTIs) with message 1; 
- No HARQ; 
- Addressed to RA-RNTI on PDCCH; 
- Conveys at least: 
  - Timing Alignment information and initial UL grant for handover; 
  - Timing Alignment information. 

The applicability of SDT is determined by MAC entity according to clause 5.27, and the applicability of NSAG-ID is determined by upper layers when the Random Access procedure is initiated [D3].

### Context

**[D1] 36300.docx**

sed random access procedure is outlined on Figure 10.1.5.2-1 below: Figure 10.1.5.2-1: Non-contention based Random Access Procedure The three steps of the non-contention based random access procedures are: 0) Random Access Preamble assignment via dedicated signalling in DL: - eNB assigns to UE a non-contention Random Access Preamble (a Random Access Preamble not within the set sent in broadcast signalling). - Signalled via: - HO command generated by target eNB and sent via source eNB for handover; - PDCCH in case of DL data arrival or positioning; - PDCCH for initial UL time alignment for a sTAG. 1) Random Access Preamble on RACH in uplink: - UE transmits the assigned non-contention Random Access Preamble. 2) Random Access Response on DL-SCH: - Semi-synchronous (within a flexible window of which the size is two or more TTIs) with message 1; - No HARQ; - Addressed to RA-RNTI on PDCCH; - Conveys at least: - Timing Alignment information and initial UL grant for handover; - Timing Alignmen

**[D2] 38300.docx**

H resources with feature(s) applicable to a Random Access procedure: Network Slicing (see clause 16.3), (e)RedCap (see clause 16.13), SDT (see clause 18), and NR coverage enhancement (see clause 19). A set of RACH resources associated with a feature is only valid for random access procedures applicable to at least that feature; and a set of RACH resources associated with several features is only valid for random access procedures having at least all of these features. The UE selects the set(s) of applicable RACH resources, after uplink carrier (i.e. NUL or SUL) and BWP selection and before selecting the RA type. When CA is configured, random access procedure with 2-step RA type is only performed on SpCell while contention resolution can be cross-scheduled by the SpCell. When CA is configured, for random access procedure with 4-step RA type, the first three steps of CBRA always occur on the SpCell while contention resolution (step 4) can be cross-scheduled by the SpCell. The three steps of a CFRA started on the SpCell remain on the SpCell.

**[D3] 38321.docx**

his Random Access procedure. 1 else if Msg1 repetition is applicable for the current Random Access procedure: 2 PRACH occasions configured by rach-ConfigAdapt in RACH-ConfigCommon of a set of Random Access resources associated with Msg1 repetition indication (as specified in clause 5.1.1c) are not applicable for this Random Access procedure. 1 else: 2 PRACH occasions configured by rach-ConfigAdapt in RACH-ConfigCommon of a set of Random Access resources are applicable for this Random Access procedure, if available (as specified in TSs 38.213 [6] and 38.212 [9]). NOTE 1: Void. 1 if neither contention-free Random Access Resources nor Random Access Resources for SI request have been provided for this Random Access procedure and one or more of the features including (e)RedCap and/or Slicing and/or SDT and/or MSG3 repetition and/or MSG1 repetition is applicable for this Random Access procedure: NOTE 2: The applicability of SDT is determined by MAC entity according to clause 5.27. The applicability of NSAG-ID is determined by upper layers when the Random Access procedure is initiated.

**[D4] 36331.docx**

Random Access channel NPSS Narrowband Primary Synchronization Signal NPUSCH Narrowband Physical Uplink Shared channel NR NR Radio Access NRS Narrowband Reference Signal NSSAI Network Slice Selection Assistance Information NSSS Narrowband Secondary Synchronization Signal NTN Non-Terrestrial Network OS OFDM Symbol P2X Pedestrian-to-Everything PCCH Paging Control Channel PCell Primary Cell PDCCH Physical Downlink Control Channel PDCP Packet Data Convergence Protocol PDU Protocol Data Unit PLMN Public Land Mobile Network PMK Pairwise Master Key PO Paging Occasion posSIB Positioning SIB ProSe Proximity based Services PS Public Safety (in context of sidelink), Packet Switched (otherwise) PSCell Primary Secondary Cell PSK Pre-Shared Key PTAG Primary Timing Advance Group PUCCH Physical Uplink Control Channel PUR Preconfigured Uplink Resource QCI QoS Class Identifier QoE Quality of Experience QoS Quality of Service RACH Random Access CHannel RAI Release Assistance Indication RAT Radio Access Te

**[D5] 36213.docx**

hysical non-synchronized random access procedure From the physical layer perspective, the L1 random access procedure encompasses the transmission of random access preamble and random access response. The remaining messages are scheduled for transmission by the higher layer on the shared data channel and are not considered part of the L1 random access procedure. A random access channel occupies 6 resource blocks in a subframe or set of consecutive subframes reserved for random access preamble transmissions. The eNodeB is not prohibited from scheduling data in the resource blocks reserved for random access channel preamble transmission. A UE is not expected to be configured with PRACH on a LAA SCell. The following steps are required for the L1 random access procedure: - Layer 1 procedure is triggered upon request of a preamble transmission by higher layers. - A preamble index, a target preamble received power (PREAMBLE_RECEIVED_TARGET_POWER), a corresponding RA-RNTI and a PRACH resource are indicated by higher layers as part of the request.

## gs-020: What is the LTE X2 interface used for?

### Answer

The LTE X2 interface is used for inter-eNB communication, specifically for exchanging necessary data for the setup of the X2 interface and implicitly performing an X2 reset, as well as for mobility parameter management, load management, and reporting of general error situations [D1, D3]. 

It is also used for setting up the X2 interface, which allows for the exchange of necessary data for the eNB or en-gNB to set up the X2 interface [D1]. 

Additionally, the X2 interface is used for energy saving, allowing the indication of cell activation/deactivation over the X2 interface [D1]. 

However, the context does not provide enough information to determine the exact purpose of the X2 interface in the LTE network.

### Context

**[D1] 36423.docx**

lows reporting of general error situations, for which function specific error messages have not been defined. - Resetting the X2. This function is used to reset the X2 interface. - Setting up the X2. This function is used to exchange necessary data for the eNB or en-gNB for setup the X2 interface and implicitly perform an X2 Reset. - eNB Configuration Update. This function allows updating of application level data needed for two eNBs to interoperate correctly over the X2 interface. - Mobility Parameters Management. This function allows the eNB to coordinate adaptation of mobility parameter settings with a peer eNB. - Mobility Robustness Optimisation. This function allows reporting of information related to mobility failure events. - Energy Saving. This function allows decreasing energy consumption by enabling indication of cell activation/deactivation over the X2 interface. - X2 Release. This function allows an eNB to be aware that the signalling connection to a peer eNB is unavailable. - Message Transfer. This function allows indirect transport of X2AP messages to a peer eNB.

**[D2] 36423.docx**

en editorial only changes have been incorporated in the document. ## 1 Scope The present document specifies the radio network layer signalling procedures of the control plane between eNBs in E-UTRAN. X2AP supports the functions of X2 interface by signalling procedures defined in this document. X2AP is developed in accordance to the general principles stated in TS 36.401 [2] and TS 36.420 [3]. ## 2 References The following documents contain provisions which, through reference in this text, constitute provisions of the present document. - References are either specific (identified by date of publication, edition number, version number, etc.) or non-specific. - For a specific reference, subsequent revisions do not apply. - For a non-specific reference, the latest version applies. In the case of a reference to a 3GPP document (including a GSM document), a non-specific reference implicitly refers to the latest version of that document in the same Release as the present document. [1] 3GPP TR 21.905: Vocabulary for 3GPP Specifications.

**[D3] 36300.docx**

s are used in LTE, security is stopped after the handover. For inter-RAT handover to LTE, security is activated after the handover with NULL algorithms if security is not activated in the source RAT. ## 23.2 Subscriber and equipment trace ## 23.2.0 General Support for subscriber and equipment trace for E-UTRAN and EPC shall be as specified in TS 32.421 [29], TS 32.422 [30] and TS 32.423 [31]. ## 23.2.1 Signalling activation All traces are initiated by the core network, even if the trace shall be carried out in the radio network. If the eNB has received an UE CONTEXT RELEASE COMMAND message where the UE is associated to an E-UTRAN Trace Id then the eNB shall terminate the on-going Trace. The following functionality is needed on the S1 and X2 interface: - Support for inclusion of subscriber and equipment trace information in INITIAL CONTEXT SETUP REQUEST message over the S1 interface. - Support for an explicit TRACE START message over the S1 interface. - Support for inclusion of subscriber and equipment trace information in the HANDOVER REQUEST message over the X2 interface.

**[D4] 36401.docx**

lane ## 5.3 Control plane Figure 5.3-1 shows the control plane (signalling) protocol stacks on S1 and Uu interfaces. Note 1: The radio interface protocols are defined in 3GPP TS 36.2xx and TS 36.3xx. Note 2: The protocol is defined in 3GPP TS 36.41x. (Description of S1 interface). Note 3: EMM, ESM: This exemplifies a set of NAS control protocols between UE and EPC. The evolution of the protocol architecture for these protocols is outside the scope of the present document. Figure 5.3-1: S1 and Uu control plane NOTE: Both the Radio protocols and the S1 protocols contain a mechanism to transparently transfer NAS messages. ## 6 E-UTRAN architecture ## 6.1 Overview Figure 6.1-1 Overall architecture The LTE architecture can be further described as follows: The E-UTRAN consists of a set of eNBs connected to the EPC through the S1. An eNB can support FDD mode, TDD mode or dual mode operation. eNBs can be interconnected through the X2. S1 and X2 are logical interfaces. The E-UTRAN is layered into a Radio Network Layer (RNL) and a Transport Network Layer (TNL). The E-UTRAN architecture, i.e.

**[D5] 36423.docx**

36.422 [21]. ## 7 Functions of X2AP The X2AP protocol provides the following functions: - Mobility Management. This function allows the eNB to move the responsibility of a certain UE to another eNB. Forwarding of user plane data, Status Transfer and UE Context Release function are parts of the mobility management. - Dual Connectivity. This function allows the eNB to request another eNB to provide radio resources for a certain UE while keeping responsibility for that UE. - E-UTRA-NR Dual Connectivity. This function allows the eNB to request another en-gNB to provide radio resources for a certain UE while keeping responsibility for that UE. - Load Management. This function is used by eNBs to indicate resource status, overload and traffic load to each other. - Reporting of General Error Situations. This function allows reporting of general error situations, for which function specific error messages have not been defined. - Resetting the X2. This function is used to reset the X2 interface. - Setting up the X2.

## gs-022: What is SDAP and what role does it play in 5G?

### Answer

SDAP (Service Data Adaptation Protocol) is a protocol that maps between a QoS flow and a data radio bearer, marking QoS flow IDs (QFI) in both downlink (DL) and uplink (UL) packets. This protocol is part of the 5G System and is used to provide quality of service (QoS) forwarding treatment. SDAP is configured for each individual PDU session and is used to provide secure element and exchanges N1 signalling with the 5GC. 

SDAP plays a crucial role in the 5G System by providing a unified authentication framework, supporting stateless NFs, and enabling concurrent access to local and centralized services. It is also used to support roaming with both Home routed traffic as well as Local breakout traffic in the visited PLMN. 

SDAP is defined in TS 36.331 [D2] and TS 23.501 [D1, D3].

### Context

**[D1] 23501.docx**

PP access and non-3GPP access. - Support a unified authentication framework. - Support stateless NFs, where the compute resource is decoupled from the storage resource. - Support capability exposure. - Support concurrent access to local and centralized services. To support low latency services and local access to data networks, UP functions can be deployed close to the Access Network. - Support roaming with both Home routed traffic as well as Local breakout traffic in the visited PLMN. ## 4.2 Architecture reference model ## 4.2.1 General This specification describes the architecture for the 5G System. The 5G architecture is defined as service-based and the interaction between network functions is represented in two ways. - A service-based representation, where network functions (e.g. AMF) within the Control Plane enables other authorized network functions to access their services. This representation also includes point-to-point reference points where necessary.

**[D2] 36331.docx**

Stage 3. [96] 3GPP TS 22.261: Service requirements for the 5G System. [97] 3GPP TS 37.324: Service Data Adaptation Protocol (SDAP) specification. [98] ATIS 0700041: WEA 3.0: Device-Based Geo-Fencing. [99] 3GPP TS 26.114: IP Multimedia Subsystem (IMS); Multimedia Telephony; Media handling and interaction . [100] 3GPP TS 38.101-2: NR; User Equipment (UE) radio transmission and reception; Part 2: Range 2 Standalone . [101] 3GPP TS 38.101-3: NR; User Equipment (UE) radio transmission and reception; Part 3: Range 1 and Range 2 Interworking operation with other radios. [102] 3GPP TS 23.502: Procedures for the 5G System; Stage 2. [103] 3GPP TS 38.314: NR; layer 2 measurements. [104] 3GPP TS 23.287: Architecture enhancements for 5G System (5GS) to support Vehicle-to-Everything (V2X) services . [105] 3GPP TS 38.472: NG-RAN; F1 signalling transport. [106] 3GPP TS 38.300: NR; Overall description; Stage 2. [107] 3GPP TS 38.174: NR; Integrated access and backhaul radio transmission and reception.

**[D3] 38300.docx**

6.5 SDAP Sublayer The main services and functions of SDAP include: - Mapping between a QoS flow and a data radio bearer; NOTE: When remapping an XR QoS flow carrying PDU sets (see clause 16.15) from one DRB to another (as exemplified in Annex A), all SDAP SDUs belonging to a PDU Set should be mapped to the same DRB. - Marking QoS flow ID (QFI) in both DL and UL packets. A single protocol entity of SDAP is configured for each individual PDU session. ## 6.6 L2 Data Flow An example of the Layer 2 Data Flow is depicted on Figure 6.6-1, where a transport block is generated by MAC by concatenating two RLC PDUs from RBx and one RLC PDU from RBy. The two RLC PDUs from RBx each corresponds to one IP packet (n and n1) while the RLC PDU from RBy is a segment of an IP packet (m). NOTE: H depicts the headers and subheaders. Figure 6.6-1: Data Flow Example ## 6.7 Carrier Aggregation In case of CA, the multi-carrier nature of the physical layer is only exposed to the MAC layer for which one HARQ ent

**[D4] 23501.docx**

configuration, etc.). Providing different QoS forwarding treatment requires separate 5G QoS Flow. 5G QoS Identifier: A scalar that is used as a reference to a specific QoS forwarding behaviour (e.g. packet loss rate, packet delay budget) to be provided to a 5G QoS Flow. This may be implemented in the access network by the 5QI referencing node specific parameters that control the QoS forwarding treatment (e.g. scheduling weights, admission thresholds, queue management thresholds, link layer protocol configuration, etc.). 5G System: 3GPP system consisting of 5G Access Network (AN), 5G Core Network and UE. 5G-BRG: The 5G-BRG is a 5G-RG defined in BBF. 5G-CRG: The 5G-CRG is a 5G-RG specified in DOCSIS MULPI [89]. 5G-RG: A 5G-RG is a RG capable of connecting to 5GC playing the role of a UE with regard to the 5G core. It supports secure element and exchanges N1 signalling with 5GC. The 5G-RG can be either a 5G-BRG or 5G-CRG.

**[D5] 38331.docx**

User Equipment (UE) radio transmission and reception; Part 1: Range 1 Standalone. [16] 3GPP TS 38.211: NR; Physical channels and modulation. [17] 3GPP TS 38.212: NR; Multiplexing and channel coding. [18] ITU-T Recommendation X.683 (08/2015) Information Technology  Abstract Syntax Notation One (ASN.1): Parameterization of ASN.1 specifications (Same as the ISO/IEC International Standard 8824-4). [19] 3GPP TS 38.214: NR; Physical layer procedures for data. [20] 3GPP TS 38.304: NR; User Equipment (UE) procedures in Idle mode and RRC Inactive state. [21] 3GPP TS 23.003: Numbering, addressing and identification. [22] 3GPP TS 36.101: E-UTRA; User Equipment (UE) radio transmission and reception. [23] 3GPP TS 24.501: Non-Access-Stratum (NAS) protocol for 5G System (5GS); Stage 3. [24] 3GPP TS 37.324: Service Data Adaptation Protocol (SDAP) specification. [25] 3GPP TS 22.261: Service requirements for the 5G System. [26] 3GPP TS 38.306: User Equipment (UE) radio access capabilities. [27] 3GPP TS 36.304: E-UTRA; User Equipment (UE) procedures in idle mode.

## gs-023: What is NSSAI and how does 5G network slicing work at RAN level?

### Answer

NSSAI stands for Network Slice Specific Access Information, which is a set of information that defines the access information for a specific Network Slice (TS 23.501, [D1]).

At the RAN level, network slicing is realized by providing different L1/L2 configurations to different network slices (TS 38.300, [D3]). The RAN part of a network slice consists of the radio access network, which includes the baseband unit, the radio unit, and the radio frequency unit (TS 38.300, [D3]).

The support of network slicing relies on the principle that traffic for different slices is handled by different PDU sessions (TS 38.300, [D3]). The RAN part of a network slice is configured to support the specific access information for that slice, which includes the NSSAI (TS 23.501, [D1]).

The NSSAI is used by the RAN for AMF selection, as described in clause 6.3.5 (TS 23.501, [D4]). The Requested NSSAI is used by the UE to request a specific access type, and the RAN uses this information to select the AMF (TS 23.501, [D4]).

In summary, NSSAI is a set of information that defines the access information for a specific Network Slice, and it is used by the RAN to configure the radio access network and select the AMF for a specific access type.

### Context

**[D1] 23501.docx**

f the S-NSSAI needs to be available in at least a cell of the TA. A Network Slice is considered available in a TA if the Network Slice is supported within the TA and available in all cells of the TA. In addition, policies in the NSSF may further restrict from using certain Network Slices in a particular TA, e.g. depending on the HPLMN of the UE. The UE can receive, for a Network Slice where the NS-AoS does not match the whole set of cells in one or more TAs, S-NSSAI location availability information as described in clause 5.15.18. The support of a Network Slice in a TA is established end-to-end using a combination of OAM and signalling among network functions. It is derived by using the S-NSSAIs supported per TA in 5G-AN, the S-NSSAIs supported in the AMF and operator policies per TA in the NSSF. The AMF learns the S-NSSAIs supported per TA by the 5G-AN when the 5G-AN nodes establish or update the N2 connection with the AMF (see TS 38.413 [34]) and TS 38.300 [27]). One or all AMF per AMF Set provides and updates the NSSF with the S-NSSAIs support per TA.

**[D2] 23501.docx**

work Slice may be supported in the whole PLMN or in one or more Tracking Areas of the PLMN. A Network Slice is supported within a TA if the 5G-AN has been configured to support the S-NSSAI in the TA. Network Slices are defined to be available within an NS-AoS when the Network Slice is supported in the set of TAs which the NS-AoS comprises and more than zero resources are allocated to the Network Slice in the NG-RAN cells of the NS-AoS. An NS-AoS can be defined on a per cell level granularity when the NS-AoS is not matching deployed Tracking Areas as defined in clause 5.15.18. The availability of a Network Slice S-NSSAI in an NS-AoS requires the support of the S-NSSAI in the involved NFs and in the NG-RAN in the TAs which the NS-AoS comprises. Hence, the cells of a TA need to be configured to support a S-NSSAI if the S-NSSAI needs to be available in at least a cell of the TA. A Network Slice is considered available in a TA if the Network Slice is supported within the TA and available in all cells of the TA.

**[D3] 38300.docx**

tness of the transmission for coverage enhancement. Such relaxation may be achieved when a UE in good coverage indicates a preference to the gNB to reduce the local air interface delay by sending a DelayBudgetReport message to decrease the DRX cycle length, so that the E2E delay and jitter can be reduced. When the UE detects changes such as end-to-end MMTEL voice quality or local radio quality, the UE may inform the gNB its new preference by sending DelayBudgetReport messages with updated contents. ## 16.3 Network Slicing ## 16.3.1 General Principles and Requirements In this clause, the general principles and requirements related to the realization of network slicing in the NG-RAN for NR connected to 5GC and for E-UTRA connected to 5GC are given. A network slice always consists of a RAN part and a CN part. The support of network slicing relies on the principle that traffic for different slices is handled by different PDU sessions. Network can realise the different network slices by scheduling and also by providing different L1/L2 configurations.

**[D4] 23501.docx**

on, the 5GC is responsible for selection of a Network Slice instance(s) to serve a UE including the 5GC Control Plane and User Plane Network Functions corresponding to this Network Slice instance(s). The Subscription Information may contain restrictions to the simultaneous registration of network slices. This is provided to the serving AMF as part of the UE subscription, in the form of Network Slice Simultaneous Registration Group (NSSRG) information (see clause 5.15.12). The (R)AN may use Requested NSSAI in access stratum signalling to handle the UE Control Plane connection before the 5GC informs the (R)AN of the Allowed NSSAI. The Requested NSSAI is used by the RAN for AMF selection, as described in clause 6.3.5. The UE shall not include the Requested NSSAI in the RRC Resume when the UE asks to resume the RRC connection and is CM-CONNECTED with RRC_INACTIVE state. When a UE is successfully registered over an Access Type, the CN informs the (R)AN by providing the Allowed NSSAI for the corresponding Access Type.

**[D5] 23502.docx**

iodic Registration Timer Indication], [LADN Information], [MICO Indication], [IMS Voice over PS session supported Indication], [Emergency Service Support indicator], [Accepted DRX parameters for E-UTRA and NR], [Accepted DRX parameters for NB-IoT], [extended idle mode DRX parameters], [Paging Time Window], [Network support of Interworking without N26], [Access Stratum Connection Establishment NSSAI Inclusion Mode], [Network Slicing Subscription Change Indication], [Operator-defined access category definitions], [List of equivalent PLMNs], [Enhanced Coverage Restricted information], [Supported Network Behaviour], [Service Gap Time], [PLMN-assigned UE Radio Capability ID], [PLMN-assigned UE Radio Capability ID deletion], [WUS Assistance Information], [AMF PEIPS Assistance Information], [AMF LP-WUSPS Assistance Information], [LP-WUS Disabled indication], [Truncated 5G-S-TMSI Configuration], [Connection Release Supported], [Paging Cause Indication for Voice Service Supported], [Paging Rest

## gs-024: What is the SSB (Synchronization Signal Block) in NR?

### Answer

The SSB (Synchronization Signal Block) in NR refers to the block of symbols that carries the primary and secondary synchronization signals (PSS, SSS) and the Physical Broadcast Channel (PBCH) block. [D3]

The SSB block is transmitted across 3 OFDM symbols and 240 subcarriers, but on one symbol leaving an unused part in the middle for SSS. [D3]

The possible time locations of SSBs within a half-frame are determined by sub-carrier spacing and the periodicity of the half-frames where SSBs are transmitted is configured by the network. [D3]

The SSB block is used for synchronization and is transmitted in different spatial directions (i.e. using different beams, spanning the coverage area of a cell) within the frequency span of a carrier. [D3]

The SSB block is also used for NR Dual Connectivity, where it is transmitted in conjunction with the Secondary Cell Group (SCG) and the Secondary Cell (SCell). [D4]

The SSB block is also used for NR-DC (NR Dual Connectivity) and is transmitted in conjunction with the Primary Cell (PCell) and the Secondary Cell (SCell). [D4]

Note that the SSB block is not explicitly defined in the provided context excerpts, but rather is described in relation to other NR concepts such as SSB periodicity, SS/PBCH block measurement timing configuration, and NR Dual Connectivity.

### Context

**[D1] 36331.docx**

9)). If not configured, the UE chooses a random value as rmtc-SubframeOffsetNR for measDurationNR which shall be selected to be between 0 and the configured rmtc-PeriodicityNR with equal probability. rs-ConfigSSB Indicates the SSB configuration for measuring the set of SS blocks within the SMTC measurement duration. ssb-PositionQCL-NR Indicates the QCL relationship between SS/PBCH blocks for a specific neighbor cell as specified in TS 38.213 [88], clause 4.1. If provided, the cell specific value overwrites the common value signalled by ssb-PositionQCL-CommonNR in MeasObjectNR for the indicated cell. ssb-PositionQCL-CommonNR Indicates the QCL relationship between SS/PBCH blocks for NR neighbor cells as specified in TS 38.213 [88], clause 4.1. If ssb-PositionQCL-CommonNR-r17 is present, the UE shall ignore ssb-PositionQCL-CommonNR-r16. subcarrierSpacingSSB Subcarrier spacing of SSB. Only the following values are applicable depending on the used frequency: FR1: 15 or 30 kHz FR2-1: 120 or

**[D2] 36331.docx**

nnelNumber-r15 INTEGER (1..20), sensingPeriodicity-r15 ENUMERATED ms20, ms50, ms100, ms200, ms300, ms400, ms500, ms600, ms700, ms800, ms900, ms1000, sensingReselectionCounter-r15 INTEGER (5..75), sensingPriority-r15 INTEGER (1..8)  -- ASN1STOP ##  MTC-SSB-NR The IE MTC-SSB-NR specifies the SS/PBCH block measurement timing configuration (SMTC) applicable for SSB based NR measurements i.e. the time occasions for performing these measurements, see 5.5.2.13. MTC-SSB-NR information elements -- ASN1START MTC-SSB-NR-r15 :: SEQUENCE  periodicityAndOffset-r15 CHOICE  sf5-r15 INTEGER (0..4), sf10-r15 INTEGER (0..9), sf20-r15 INTEGER (0..19), sf40-r15 INTEGER (0..39), sf80-r15 INTEGER (0..79), sf160-r15 INTEGER (0..159) , ssb-Duration-r15 ENUMERATED sf1, sf2, sf3, sf4, sf5   MTC-SSB2-LP-NR-r16:: SEQUENCE  pci-List-r16 SEQUENCE (SIZE (1..maxNrofPCI-PerSMTC-r16)) OF PhysCellIdNR-r15 OPTIONAL, -- Need OR periodicity-r16 ENUMERATED sf10, sf20, sf40, sf80, sf160, spare3, spare2, spare1  -- ASN1STOP ##

**[D3] 38300.docx**

er of CCEs and coded bits, and corresponds to the same DCI payload. Polar coding is used for PDCCH. Each resource element group carrying PDCCH carries its own DMRS. QPSK modulation is used for PDCCH. ## 5.2.4 Synchronization signal and PBCH block The Synchronization Signal and PBCH block (SSB) consists of primary and secondary synchronization signals (PSS, SSS), each occupying 1 symbol and 127 subcarriers, and PBCH spanning across 3 OFDM symbols and 240 subcarriers, but on one symbol leaving an unused part in the middle for SSS as show in Figure 5.2.4-1. For the 3 MHz channel bandwidth, the PBCH is further equally punctured from both edges to span 144 subcarriers. The possible time locations of SSBs within a half-frame are determined by sub-carrier spacing and the periodicity of the half-frames where SSBs are transmitted is configured by the network. During a half-frame, different SSBs may be transmitted in different spatial directions (i.e. using different beams, spanning the coverage area of a cell). Within the frequency span of a carrier, multiple SSBs can be transmitted.

**[D4] 38213.docx**

ermination NDI New Data Indicator NE-DC NR E-UTRA Dual Connectivity with MCG using NR and SCG using E-UTRA NR-DC NR NR Dual Connectivity PBCH Physical Broadcast Channel PCell Primary Cell PDCCH Physical Downlink Control Channel PDSCH Physical Downlink Shared Channel PO Paging Occasion PRACH Physical Random Access Channel PRB Physical Resource Block PRG Physical Resource block Group PSCell Primary Secondary Cell PSBCH Physical Sidelink Broadcast Channel PSCCH Physical Sidelink Control Channel PSFCH Physical Sidelink Feedback Channel PSS Primary Synchronization Signal PSSCH Physical Sidelink Shared Channel PUCCH Physical Uplink Control Channel PUCCH-SCell PUCCH SCell PUCCH-sSCell PUCCH switching SCell PUSCH Physical Uplink Shared Channel QCL Quasi Co-Location RB Resource Block RE Resource Element RLM Radio Link Monitoring RRM Radio Resource Management RS Reference Signal RSRP Reference Signal Received Power SBFD Sub-Band Full Duplex SCG Secondary Cell Group SCI Sidelink Control Informati

**[D5] 38331.docx**

ds to the number of full radio frames counted from the beginning of a radio frame #0 of serving cell to the beginning of the closest subsequent radio frame #0 of the cell in which SSB is transmitted. sfn-SSB-Offset Indicates the SFN offset of the transmitted SSB relative to the start of the SSB period. Value 0 indicates that the SSB is transmitted in the first system frame, value 1 indicates that SSB is transmitted in the second system frame and so on. The network configures this field according to the field ssb-Periodicity such that the indicated system frame does not exceed the configured SSB periodicity. ssb-Freq Indicates the frequency of the SSB. ss-PBCH-BlockPower Average EPRE of the resources elements that carry secondary synchronization signals in dBm that the NW used for SSB transmission, see TS 38.213 [13], clause 7. ssb-Periodicity Indicates the periodicity of the SSB. If the field is absent, the UE applies the value ms5. (see TS 38.213 [13], clause 4.1) ssbSubcarrierSpacing Subcarrier spacing of SSB.

## gs-025: What are the differences between NR and LTE physical layer?

### Answer

The physical layer of 5G New Radio (NR) has several differences compared to the physical layer of Long-Term Evolution (LTE). 

One key difference is the use of orthogonal frequency-division multiplexing (OFDM) in NR, whereas LTE uses a combination of OFDM and single-carrier frequency-division multiplexing (SC-FDMA) [D1, D2]. 

Another difference is the use of a more efficient coding scheme in NR, such as low-density parity-check (LDPC) codes, whereas LTE uses turbo codes [D1, D3]. 

Additionally, NR has a more flexible and adaptive transmission scheme, with the ability to switch between different transmission modes, such as high-speed data transmission and low-speed data transmission [D1, D3]. 

It's worth noting that the physical layer of NR is designed to support a wider range of frequencies and higher data rates than LTE, with support for frequencies from 0.5 GHz to 100 GHz and peak data rates of up to 20 Gbps [D1, D3].

### Context

**[D1] 38213.docx**

ical layer procedures for control operations in 5G-NR. ## 2 References The following documents contain provisions which, through reference in this text, constitute provisions of the present document. [1] 3GPP TR 21.905: Vocabulary for 3GPP Specifications [2] 3GPP TS 38.201: NR; Physical Layer  General Description [3] 3GPP TS 38.202: NR; Services provided by the physical layer [4] 3GPP TS 38.211: NR; Physical channels and modulation [5] 3GPP TS 38.212: NR; Multiplexing and channel coding [6] 3GPP TS 38.214: NR; Physical layer procedures for data [7] 3GPP TS 38.215: NR; Physical layer measurements [8-1] 3GPP TS 38.101-1: NR; User Equipment (UE) radio transmission and reception; Part 1: Range 1 Standalone [8-2] 3GPP TS 38.101-2: NR; User Equipment (UE) radio transmission and reception; Part 2: Range 2 Standalone [8-3] 3GPP TS 38.101-3: NR; User Equipment (UE) radio transmission and reception; Part 3: Range 1 and Range 2 Interworking operation with other radios [8-4] 3GPP TS 38.101-4: NR;

**[D2] 36300.docx**

LTE-based 5G terrestrial broadcast | 17.0.0 | RP-95 | RP-220839 | 1362 | - | B | BLCR to 36.300_Addition of SON features enhancement | 17.0.0 2022-06 | RP-96 | RP-221738 | 1363 | 2 | B | Introduction of gNB ID length reporting in the NR CGI report [gNB_ID_Length] | 17.1.0 | RP-96 | RP-221737 | 1364 | 2 | F | IoT NTN Stage 2 Corrections | 17.1.0 | RP-96 | RP-221733 | 1366 | 1 | F | RACH optimisation in EN-DC secondary cell | 17.1.0 | RP-96 | RP-221733 | 1368 | 1 | F | Correction on R17 SON MDT for TS36.300 | 17.1.0 2022-09 | RP-97 | RP-222522 | 1369 | 1 | F | Correction to IoT NTN stage 2 description | 17.2.0 2022-12 | RP-98 | RP-223405 | 1373 | 1 | A | Correction on measurement reporting for interference detection in UAV | 17.3.0 | RP-98 | RP-223414 | 1374 | - | F | Removal of FFS from LTE Relay description | 17.3.0 | RP-98 | RP-223409 | 1375 | 2 | F | IoT NTN corrections | 17.3.0 | RP-98 | RP-223409 | 1376 | - | F | Correction to IoT NTN about constructing the Mapped Cell ID | 17.3.0

**[D3] 38214.docx**

torial only changes have been incorporated in the document. ## 1 Scope The present document specifies and establishes the characteristics of the physicals layer procedures of data channels for 5G-NR. ## 2 References The following documents contain provisions which, through reference in this text, constitute provisions of the present document. [1] 3GPP TR 21.905: Vocabulary for 3GPP Specifications [2] 3GPP TS 38.201:  NR; Physical Layer  General Description [3] 3GPP TS 38.202: NR; Services provided by the physical layer [4] 3GPP TS 38.211: NR; Physical channels and modulation [5] 3GPP TS 38.212: NR; Multiplexing and channel coding [6] 3GPP TS 38.213: NR; Physical layer procedures for control [7] 3GPP TS 38.215: NR; Physical layer measurements [8] 3GPP TS 38.101-1: NR; User Equipment (UE) radio transmission and reception; Part 1: Range 1 Standalone [9] 3GPP TS 38.104: NR; Base Station (BS) radio transmission and reception [10] 3GPP TS 38.321: NR; Medium Access Control (MAC) protocol spec

**[D4] 38300.docx**

nlink 47 5.2.1 Downlink transmission scheme 47 5.2.2 Physical-layer processing for physical downlink shared channel 48 5.2.3 Physical downlink control channels 48 5.2.4 Synchronization signal and PBCH block 49 5.2.5 Physical layer procedures 50 5.2.5.1 Link adaptation 50 5.2.5.2 Power Control 50 5.2.5.3 Cell search 50 5.2.5.4 HARQ 51 5.2.5.5 Reception of SIB1 51 5.2.6 Downlink Reference Signals and Measurements for Positioning 51 5.3 Uplink 51 5.3.1 Uplink transmission scheme 51 5.3.2 Physical-layer processing for physical uplink shared channel 52 5.3.3 Physical uplink control channel 52 5.3.4 Random access 54 5.3.5 Physical layer procedures 54 5.3.5.1 Link adaptation 54 5.3.5.2 Uplink Power control 54 5.3.5.3 Uplink timing control 54 5.3.5.4 HARQ 55 5.3.5.5 Prioritization of overlapping transmissions 55 5.3.6 Uplink Reference Signals and Measurements for Positioning 55 5.4 Carrier aggregation 55 5.4.1 Carrier aggregation 55 5.4.2 Supplementary Uplink 56 5.4.3 Uplink Tx switching 56 5.

**[D5] 38215.docx**

coding [5] 3GPP TS 38.213: NR; Physical layer procedures for control channels [6] 3GPP TS 38.214: NR; Physical layer procedures for data channels [7] 3GPP TS 38.321: NR; Medium Access Control (MAC) protocol specification [8] 3GPP TS 38.331: NR; Radio Resource Control (RRC); Protocol specification [9] 3GPP TS 38.104: NR; Base Station (BS) radio transmission and reception [10] 3GPP TS 36.331: Evolved Universal Terrestrial Radio Access (E-UTRA); Radio Resource Control (RRC); Protocol specification [11] IEEE 802.11, Part 11: Wireless LAN Medium Access Control (MAC) and Physical Layer (PHY) specifications, IEEE Std. [12] 3GPP TS 38.133: NR; Requirements for support of radio resource management [13] 3GPP TS 36.211: Evolved Universal Terrestrial Radio Access (E-UTRA); Physical channels and modulation [14] 3GPP TS 38.509: 5GS; Special conformance testing functions for User Equipment (UE) [15] 3GPP TS 38.901: Study on channel model for frequencies from 0.5 to 100 GHz [16] 3GPP TS 38.455: NR Pos
