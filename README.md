# Peer-to-Peer File Distribution System

## Overview

This system is designed to efficiently distribute files across a network of peers using a centralized server for file/chunk tracking. Peers can share chunks of their files with each other, while the server acts as a middle-man keeping track of the chunks and their owners. This system uses multithreading to showcase that peers can simultaneously upload and download chunks of files. The server and peers are designed with object-oriented principles.

### System Components:

- **Server**: 
    - Facilitates communication between peers.
    - Logs which files exist and which peers own chunks of those files.
    - Does not store file data; only stores pointers to the peers holding the data.
    - Responds to peers’ requests for file locations.

- **Peers**: 
    - Download and upload file chunks from/to other peers.
    - Request file chunk locations from the server and then directly contact peers to request specific chunks.
    - Can upload chunks to other peers while simultaneously downloading from others.
    - After downloading all chunks of a file, the peer combines the chunks into a complete file.

## File Chunking and Distribution

Each line in a text file is treated as a chunk. This allows peers to download parts of a file from multiple different peers, distributing the load across the network.

- Each chunk is assigned a `chunk_id` and stored in a hashmap (dictionary).
    - Example: A file with 3 chunks is stored as:
      ```python
      {0 : "chunk 0 info", 1 : "chunk 1 info", 2 : "chunk 2 info"}
      ```

- Upon downloading a chunk, peers register their ownership of that chunk with the server.

## File Download Process

### Requests:
- When a peer wants to download a file, it sends a `FileLocationsRequest` to the server. 
- The server responds with a list of peers that have chunks of the requested file.
- The peer then contacts other peers directly to request specific chunks using `FileChunkRequest`.

### Downloads:
- Peers download file chunks in parallel from different peers. 
- Each chunk is verified using a SHA-256 hash to ensure data integrity. 
- The downloaded chunks are stored locally on the peer, and the peer informs the server of the newly acquired chunks using `ChunkRegisterRequest`.

## Communication Protocol

All requests are prefixed with the requesting peer’s port number to simplify book-keeping. Each part of the message is separated by a space.

- **RegisterRequest**: Registers ownership of a file and its chunks with the server. 
    - Example: `50001 RegisterRequest recipe.txt:5`
- **FileListRequest**: Retrieves a list of all available files on the network.
- **FileLocationsRequest**: Requests the locations of peers that hold chunks of a specific file. 
    - Example: `50002 FileLocationsRequest recipe.txt`
- **FileChunkRequest**: Requests a specific chunk of a file from a peer. 
    - Example: `50003 FileChunkRequest 50001-recipe.txt-0`
- **ChunkRegisterRequest**: Informs the server that the peer now owns a specific chunk. 
    - Example: `50002 ChunkRegisterRequest recipe.txt<>1`

## Program Structure

### Server Class:
- **Attributes**:
    - `HOST` and `PORT`: Address and port for the server.
    - `fileOwners`: Dictionary mapping file names to dictionaries of peers and their chunks.
- **Methods**:
    - `start_server()`: Starts the server, listens for peer connections, and spawns threads to handle each peer.
    - `handle_client()`: Processes peer requests for file registration, chunk requests, and file location requests.
    - `RegisterRequest()`: Handles file and chunk registration from peers.
    - `FileListRequest()`: Returns the list of files on the network.
    - `FileLocationsRequest()`: Provides information about which peers have specific chunks.
    - `updateOwners()`: Updates the `fileOwners` dictionary when a peer registers a chunk.

### Peer Class:
- **Attributes**:
    - `host` and `port`: Address and port for the peer’s server.
    - `storage`: Dictionary storing downloaded file chunks.
    - `files`: Dictionary holding the initial files owned by the peer.
    - `neededChunks`: Dictionary mapping chunk IDs to a list of peers that have those chunks.
- **Methods**:
    - `start_server()`: Starts the peer’s server to handle file chunk requests.
    - `handle_client()`: Handles incoming chunk requests from other peers.
    - `send_to_peer()`: Sends a request to another peer for a chunk.
    - `send_to_server()`: Communicates with the central server to register chunks or request file locations.
    - `fileChunkRequest()`: Requests a specific chunk from another peer.
    - `downloadFile()`: Downloads all chunks of a file, verifies integrity, and reassembles the file.
    - `downloadChunk()`: Saves a downloaded chunk locally and registers it with the server.
    - `verifyHash()`: Verifies the integrity of a downloaded chunk using a SHA-256 hash.
    - `buildFile()`: Reassembles the file from its chunks.
